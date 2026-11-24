using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Ports;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;

// One bounded, read-only transaction for the native LabVIEW scan loop.
internal static class Telemetry {
    const int Port = 44820;
    const string BenchAddress = "uno";
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static readonly string[] Modes = { "OFF", "MANUAL", "AUTO", "MODE UNKNOWN / CONFLICT" };
    static readonly string[] Stages = { "Disarmed", "Armed", "Roughing", "Isolating roughing path",
        "High vacuum", "Preparing to vent", "Venting", "Closing let-up", "Fault latched" };

    static uint Number(string field, uint maximum) {
        uint value;
        if (!uint.TryParse(field, NumberStyles.None, Inv, out value) || value > maximum)
            throw new FormatException("Invalid controller value");
        return value;
    }
    static string[] Offline(string memory,string reason) {
        return new[] { memory,"OFFLINE - "+reason,"Unknown","Unavailable","0","0","0","0","0","0","0","0","Unknown","0","0" };
    }
    static void Record(string[] row,string[] fields) {
        string directory=Environment.GetEnvironmentVariable("MAIZE_LOG_DIRECTORY");
        if(string.IsNullOrWhiteSpace(directory))
            directory=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"MAIZE Vacuum","Logs");
        try {
            Directory.CreateDirectory(directory);
            DateTime now=DateTime.UtcNow;
            string address=row[0].Split(',')[0];
            string path=Path.Combine(directory,now.ToString("yyyy-MM-dd",Inv)+"-"+address+".csv");
            using(var stream=new FileStream(path,FileMode.OpenOrCreate,FileAccess.Write,FileShare.Read)) {
                stream.Seek(0,SeekOrigin.End);
                using(var writer=new StreamWriter(stream,new UTF8Encoding(false))) {
                    if(stream.Length==0) {
                        string pressureColumn=address==BenchAddress ? "bench_pressure_input,bench_age_ms" : "pressure_torr,gauge_age_ms";
                        writer.WriteLine("utc,link,sequence,uptime_ms,mode,stage,selectors,positions,attempt,status,site,events,active,latched,open_outputs,"+pressureColumn+",known_selectors");
                    }
                    string measurements=fields==null ? new string(',',15) : string.Join(",",fields,2,16);
                    writer.WriteLine(now.ToString("o",Inv)+","+row[1]+","+measurements);
                }
            }
        } catch(UnauthorizedAccessException) {
            row[1]+=" / CSV access denied";
        } catch(IOException) {
            row[1]+=" / CSV write failed";
        } catch(ArgumentException) {
            row[1]+=" / CSV path invalid";
        }
    }
    static string[] Decode(string wire,string nonce,string address,string previous) {
        bool bench=address==BenchAddress;
        string[] f=wire.Split(',');
        if (f.Length!=18 || f[0]!=(bench?"UNO3":"MAIZE3") || f[1]!=nonce)
            throw new FormatException("Controller protocol or transaction mismatch");
        uint seq=Number(f[2],uint.MaxValue), ms=Number(f[3],uint.MaxValue);
        uint age=Number(f[16],uint.MaxValue), known=Number(f[17],15);
        uint mode=Number(f[4],3), stage=Number(f[5],8);
        uint selectors=Number(f[6],15), positions=Number(f[7],255);
        for(int i=0;i<2;i++) {
            uint bit=1u<<i;
            uint expected=(known&bit)==0 ? 0u : (selectors&bit)!=0 ? 2u : 1u;
            if(((positions>>(2*i))&3u)!=expected)
                throw new FormatException("Valve indication inconsistent with physical selector");
        }
        Number(f[8],15); Number(f[9],16383);
        Number(f[10],31); Number(f[11],511); Number(f[12],int.MaxValue);
        Number(f[13],int.MaxValue); Number(f[14],15);
        string pressure="Unavailable";
        if (f[15]!="-") {
            double p;
            if(!double.TryParse(f[15],NumberStyles.Float,Inv,out p) || !(p>0 && p<9.0e9)
                || Math.Abs(p-1100)<=1) throw new FormatException("Invalid Torr reading");
            pressure=p.ToString("G5",Inv)+(bench?" bench units / A2":" Torr   /   CG1   /   "+age+" ms");
        }
        string memory=address+","+seq.ToString(Inv)+","+ms.ToString(Inv);
        string[] old=previous.Split(',');
        if(old.Length==3 && old[0]==address) {
            uint ds=unchecked(seq-Number(old[1],uint.MaxValue)), dt=unchecked(ms-Number(old[2],uint.MaxValue));
            if(ds==0 || dt==0) return Offline(previous,"Controller sample is stale");
            if(ds>int.MaxValue || dt>int.MaxValue) return Offline(memory,"Controller restarted or sample out of order");
        }
        uint outputs=Number(f[14],15);
        string[] names={"Roughing","Let-up","Turbo","Cryo"};
        var open=new System.Collections.Generic.List<string>();
        for(int i=0;i<4;i++) {
            uint bit=1u<<i;
            if((outputs&bit)!=0) open.Add(names[i]+" OPEN");
            else if((selectors&bit)!=0) open.Add(names[i]+" request inhibited");
        }
        string outText=open.Count==0?"All opening outputs off":string.Join(", ",open.ToArray());
        var row=new[] { memory,bench?"Online   /   UNO R3 BENCH":"Online   /   "+address,Modes[mode]+"   /   "+Stages[stage],pressure,
            f[8],f[7],f[9],f[10],f[11],f[13],f[12],"1",outText,f[6],f[17] };
        Record(row,f);
        return row;
    }
    static string[] Scan(string address,string previous) {
        bool bench=address==BenchAddress;
        if (address.Length==0) return Offline("","Controller address unset in Opta.address");
        IPAddress ip;
        if(bench) ip=IPAddress.Loopback;
        else if (!Regex.IsMatch(address,@"\A[0-9]{1,3}(\.[0-9]{1,3}){3}\z") ||
            !IPAddress.TryParse(address,out ip) || ip.ToString()!=address ||
            ip.GetAddressBytes()[0]==0 || ip.GetAddressBytes()[0]>=224)
            return Offline("","Invalid IPv4 address in Opta.address");
        using (var socket=new UdpClient(AddressFamily.InterNetwork)) {
            socket.Client.ReceiveTimeout=425;
            socket.Connect(ip,Port);
            string nonce=Guid.NewGuid().ToString("N").Substring(0,8);
            byte[] query=Encoding.ASCII.GetBytes((bench?"UNO3":"MAIZE3")+" R "+nonce+"\n");
            socket.Send(query,query.Length);
            IPEndPoint peer=null;
            byte[] data=socket.Receive(ref peer);
            if(data.Length>255) throw new FormatException("Oversized controller reply");
            return Decode(Encoding.ASCII.GetString(data),nonce,address,previous);
        }
    }
    static int BridgeUno(string portName) {
        if(!Regex.IsMatch(portName,@"\ACOM[1-9][0-9]*\z",RegexOptions.IgnoreCase)) return 2;
        using(var serial=new SerialPort(portName,115200,Parity.None,8,StopBits.One)) {
            // Keep the port open across HMI scans. Opening the Uno's port can reset the board.
            serial.ReadTimeout=30;
            try { serial.Open(); }
            catch(UnauthorizedAccessException) { return 2; }
            catch(IOException) { return 2; }
            catch(ArgumentException) { return 2; }

            UdpClient listener;
            try { listener=new UdpClient(new IPEndPoint(IPAddress.Loopback,Port)); }
            catch(SocketException) { return 3; }
            using(listener) {
                var frame=new StringBuilder();
                var clock=Stopwatch.StartNew();
                long received=0;
                bool discard=false;
                string payload=null;
                var sample=new Regex(@"\AUNO3,(?:[0-9]+,){13}[0-9]+\.[0-9]{2},0,15\z");
                var query=new Regex(@"\AUNO3 R ([0-9a-f]{8})\n\z");
                while(true) {
                    try {
                        int count=Math.Max(1,Math.Min(serial.BytesToRead,512));
                        for(int i=0;i<count;i++) {
                            int b=serial.ReadByte();
                            if(b=='\n') {
                                string line=frame.ToString();
                                if(!discard && sample.IsMatch(line)) {
                                    payload=line.Substring(5);
                                    received=clock.ElapsedMilliseconds;
                                }
                                frame.Clear();
                                discard=false;
                            } else if(b!='\r' && !discard) {
                                if(frame.Length>=180 || b<32 || b>126) discard=true;
                                else frame.Append((char)b);
                            }
                        }
                    } catch(TimeoutException) {
                        // Expire the last USB sample if the board stops reporting.
                    } catch(IOException) { return 4; }
                    catch(InvalidOperationException) { return 4; }

                    if(listener.Available==0) continue;
                    IPEndPoint peer=null;
                    var request=query.Match(Encoding.ASCII.GetString(listener.Receive(ref peer)));
                    if(request.Success && payload!=null && clock.ElapsedMilliseconds-received<=650) {
                        byte[] reply=Encoding.ASCII.GetBytes("UNO3,"+request.Groups[1].Value+","+payload);
                        listener.Send(reply,reply.Length,peer);
                    }
                }
            }
        }
    }
    public static int Main(string[] args) {
        if(args.Length==2 && args[0]=="--uno-bridge") return BridgeUno(args[1]);
        string prev="";
        string address="";
        bool gap=false;
        string[] row;
        try {
            prev=Console.In.ReadToEnd().Trim();
            gap=prev.StartsWith("!");
            if(gap) prev=prev.Substring(1);
            if(!Regex.IsMatch(prev,@"\A(?:uno)?[0-9.,]{0,42}\z")) prev="";
            address=File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Opta.address")).Trim();
            row=Scan(address,prev);
        } catch(SocketException) {
            row=Offline(prev,address==BenchAddress?"UNO BENCH - no current USB sample":"No reply from Opta");
        } catch(Exception e) {
            string message=e is FormatException?e.Message:"Check the controller address file and Ethernet connection";
            row=Offline(prev,message);
        }
        if(row[11]=="0" && row[0].Length!=0) {
            if(!gap) Record(row,null);
            row[0]="!"+row[0];
        }
        Console.Write(string.Join("|",row));
        return 0;
    }
}
