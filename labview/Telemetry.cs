using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

// The native VI supplies flags, the IPv4 address and its previous state on stdin.
// Each bounded invocation returns one complete display update. Nothing runs after the VI stops.
public static class Telemetry {
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
    const int Port = 44820;
    const int Live = 1, Record = 2, Auto = 4, Arm = 8, Stop = 16, Pump = 32, Vent = 64;
    const int AirLoss = 2048, NoGauge = 8192;
    public class Memory {
        public string Source = "", Log = "", Fault = "";
        public bool Armed, Seen;
        public int Previous;
        public uint Sequence, Uptime;
    }
    public class Sample {
        public uint Sequence, Uptime, Age;
        public int Base, E1, Coil, Aux;
        public bool Expansion, GateMap;
        public string Step, Fault, Unit;
        public double Pressure = double.NaN;
    }
    static bool On(int word, int bit) { return (word & bit) != 0; }
    static bool Edge(int bits, int old, int bit) { return On(bits, bit) && !On(old, bit); }
    static string State(bool v) { return v ? "ON" : "OFF"; }
    static string Bits(int bits, int mask, bool known) { return known ? State(On(bits, mask)) : "?"; }
    static uint U(string text) { return uint.Parse(text, NumberStyles.None, Inv); }
    static int Mask(string value, int maximum) {
        uint n = U(value);
        if (n > maximum) throw new FormatException("Mask out of range");
        return (int)n;
    }
    static string Token(string s) {
        if (!Regex.IsMatch(s, @"\A[A-Z0-9_]{1,32}\z")) throw new FormatException("Invalid status");
        return s;
    }
    public static Sample Decode(string wire, string nonce) {
        string[] f = wire.Split(',');
        if (f.Length != 15 || f[0] != "MAIZE2" || f[1] != nonce)
            throw new FormatException("Unexpected protocol or transaction");
        var s = new Sample { Sequence = U(f[2]), Uptime = U(f[3]), Base = Mask(f[4],15),
            Expansion = Mask(f[5],1) == 1, E1 = Mask(f[6],65535), Coil = Mask(f[7],15),
            Aux = Mask(f[8],31), Step = Token(f[9]), Unit = Token(f[11]), Age = U(f[12]), Fault = Token(f[13]),
            GateMap = Mask(f[14],1) == 1 };
        if (s.Unit != "NATIVE" && s.Unit != "TORR") throw new FormatException("Unknown unit");
        if (f[10] != "-") {
            double p;
            if (!double.TryParse(f[10], NumberStyles.Float, Inv, out p) || !(p > 0 && p < 9e9))
                throw new FormatException("Invalid pressure");
            if (s.Unit != "TORR" || Math.Abs(p - 1100.0) > 1.0) s.Pressure = p;
        }
        return s;
    }
    static Sample Read(string host) {
        IPAddress ip;
        if (!Regex.IsMatch(host, @"\A\d{1,3}(\.\d{1,3}){3}\z") || !IPAddress.TryParse(host, out ip)
            || ip.AddressFamily != AddressFamily.InterNetwork || ip.GetAddressBytes()[0] == 0
            || ip.GetAddressBytes()[0] >= 224) throw new FormatException("Enter a unicast IPv4 address");
        using (var sock = new UdpClient(AddressFamily.InterNetwork)) {
            sock.Client.ReceiveTimeout = 430;
            sock.Connect(ip, Port);
            string nonce = Guid.NewGuid().ToString("N").Substring(0,8);
            byte[] req = Encoding.ASCII.GetBytes("MAIZE2 R " + nonce + "\n");
            sock.Send(req, req.Length);
            IPEndPoint peer = null;
            var packet = sock.Receive(ref peer);
            if (packet.Length > 256) throw new FormatException("Oversize telemetry frame");
            return Decode(Encoding.ASCII.GetString(packet), nonce);
        }
    }
    static void Trip(Memory m, string why) {
        m.Armed = false;
        if (m.Fault == "") m.Fault = why;
    }
    public static Sample Simulate(Memory m, int flags) {
        bool auto = On(flags, Auto), air = !On(flags, AirLoss), gauge = !On(flags, NoGauge);
        bool stop = On(flags, Stop);
        int selectors = (flags >> 7) & 15;
        int contacts=(flags>>14)&15; // independent dry-contact injection, no coil-to-valve assignment
        bool conflict=(contacts&3)==3 || (contacts&12)==12;
        if (auto != On(m.Previous, Auto)) m.Armed = false;
        if (stop || !air || conflict) Trip(m, stop ? "STOP" : !air ? "AIR_LOSS" : "GATE_PROOF_CONFLICT");
        if (auto && selectors != 0) Trip(m, "SELECTORS_IN_AUTO");
        if (Edge(flags, m.Previous, Arm) && !stop && air && contacts==5
            && selectors == 0 && (flags & (Pump|Vent)) == 0) {
            m.Armed = true; m.Fault = "";
        }
        int desired = 0;
        if (m.Armed && auto) {
            if (On(flags, Pump) && On(flags, Vent)) Trip(m, "CONFLICTING_STARTS");
            else if (Edge(flags,m.Previous,Pump) || Edge(flags,m.Previous,Vent))
                Trip(m,"PATH_MAP_AND_PROOF_UNKNOWN");
        } else if (m.Armed) {
            desired = selectors;
            if ((desired & (desired-1)) != 0) Trip(m,"MULTIPLE_PATHS");
            if (desired != 0 && contacts!=5) Trip(m,"BENCH_CONTACTS_NOT_NEUTRAL");
        }
        if (!m.Armed) desired = 0;
        int e1 = selectors | (auto ? 32 : 16) | (On(flags,Arm) ? 64 : 0) | (stop ? 0 : 128)
            | (On(flags,Pump) ? 256 : 0) | (On(flags,Vent) ? 512 : 0) | (air ? 1024 : 0) | 0xf800;
        return new Sample {Sequence=m.Sequence+1, Uptime=m.Uptime+500, Base=contacts, GateMap=true,
            Expansion=true, E1=e1, Coil=desired, Aux=(m.Armed ? 1:0)|(m.Fault!="" ? 12:0),
            Step=m.Armed ? (auto ? "AUTO_ARMED" : "DRY_IO_ARMED") : "DISARMED", Fault=m.Fault=="" ? "NONE":m.Fault,
            Pressure=gauge ? 0.02+0.003*Math.Sin(m.Sequence*0.17) : double.NaN, Unit="TORR"};
    }
    static string Gate(Sample s, int shift) {
        if (!s.GateMap) return "UNKNOWN - contact wiring unverified";
        bool closed = On(s.Base,1<<shift), open = On(s.Base,2<<shift);
        string proof = closed && open ? "CONFLICT" : closed ? "CLOSED" : open ? "OPEN" : "NO PROOF";
        return string.Format("{0}    CLOSED reed {1}   OPEN reed {2}",proof,closed?1:0,open?1:0);
    }
    static string Mode(Sample s) {
        if (!s.Expansion) return "UNKNOWN";
        return new[]{"OFF","MANUAL","AUTO","CONFLICT"}[(s.E1>>4)&3];
    }
    static string Log(Memory m, bool record, string source, Sample s, string quality) {
        if (!record) { m.Log=""; return "Recording off"; }
        string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"MAIZE Vacuum Logs");
        Directory.CreateDirectory(dir);
        if (m.Log=="") m.Log = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff",Inv)+"-"+Guid.NewGuid().ToString("N").Substring(0,8)+".csv";
        if (!Regex.IsMatch(m.Log,@"\A[0-9]{8}-[0-9]{6}-[0-9]{3}-[a-f0-9]{8}\.csv\z"))
            throw new FormatException("Invalid session file");
        string path = Path.Combine(dir,m.Log);
        using (var f=new FileStream(path,FileMode.Append,FileAccess.Write,FileShare.Read))
        using (var w=new StreamWriter(f,new UTF8Encoding(false))) {
            if (f.Length==0) w.WriteLine("utc,source,quality,seq,uptime_ms,gate_contact_bits,e1_ok,e1_bits,coil_cmd,aux_cmd,step,pressure,unit,age_ms,fault,gate_map_verified");
            string[] values={DateTime.UtcNow.ToString("o",Inv),source,quality,"","","","","","","","","","","","",""};
            if (s!=null) {
                string[] fields={s.Sequence.ToString(),s.Uptime.ToString(),s.Base.ToString(),s.Expansion?"1":"0",
                    s.Expansion?s.E1.ToString():"",s.Coil.ToString(),s.Aux.ToString(),s.Step,
                    double.IsNaN(s.Pressure)||s.Age>2000?"":s.Pressure.ToString("R",Inv),s.Unit,s.Age.ToString(),s.Fault,s.GateMap?"1":"0"};
                fields.CopyTo(values,3);
            }
            w.WriteLine(string.Join(",",values.Select(x=>"\""+x.Replace("\"","\"\"")+"\"")));
        }
        return path;
    }
    // Output order is the connector between the worker and the LabVIEW diagram.
    public static string Tick(int flags,string host,string previous) {
        bool live=On(flags,Live);
        string source=live ? "OPTA "+host : "SIMULATION";
        Memory m=previous.Length==0 ? new Memory() :
            Json.Deserialize<Memory>(Encoding.UTF8.GetString(Convert.FromBase64String(previous)));
        bool boundary=m.Source!=source;
        if (boundary) m=new Memory {Source=source, Previous=flags};
        Sample s=null;
        string quality=live?"LIVE":"SIMULATION";
        try {
            s=live ? Read(host) : Simulate(m,flags);
            if (live && m.Seen && s.Sequence==m.Sequence && s.Uptime>=m.Uptime)
                throw new FormatException("Controller sample counter stalled");
            if (live && m.Seen && s.Uptime<m.Uptime) quality="CLOCK RESET / WRAP";
            if (live && m.Seen && s.Sequence<m.Sequence && s.Uptime>=m.Uptime) quality="COUNTER RESET / WRAP";
            m.Sequence=s.Sequence; m.Uptime=s.Uptime; m.Seen=true;
        } catch (Exception e) { s=null; quality="GAP - "+e.Message; }
        m.Previous=flags;
        string log;
        try { log=Log(m,On(flags,Record),source,s,quality); }
        catch(Exception e) { log="LOG ERROR - "+e.Message; }
        string[] o=Enumerable.Repeat("UNKNOWN",18).ToArray();
        o[0]=Convert.ToBase64String(Encoding.UTF8.GetBytes(Json.Serialize(m)));
        o[1]=live ? source+"   /   "+quality : "SIMULATION   /   dry I/O exercise"; o[2]=log; o[3]="NaN"; o[4]="NO CURRENT SAMPLE";
        if (s!=null) {
            bool numeric=!double.IsNaN(s.Pressure) && s.Age<=2000;
            // Only Torr samples enter the pressure chart. Insert a gap on every source change.
            if (numeric && s.Unit=="TORR" && previous.Length>0 && quality!="CLOCK RESET / WRAP" && !boundary)
                o[3]=s.Pressure.ToString("R",Inv);
            o[4]=numeric ? s.Pressure.ToString("G5",Inv)+" "+s.Unit+"   /   "+s.Age+" ms" : "UNAVAILABLE / STALE";
            if (live && numeric) o[4]+="   CG1 / display only";
            o[5]=Mode(s)+"   /   "+s.Step; o[6]=s.Fault;
            o[7]=Gate(s,0); o[8]=Gate(s,2);
            o[9]=string.Join("     ",Enumerable.Range(0,4).Select(v=>"S"+(v+1)+" "+Bits(s.E1,1<<v,s.Expansion)));
            o[10]=string.Join("     ",Enumerable.Range(0,4).Select(v=>"R"+(v+1)+" "+State(On(s.Coil,1<<v))));
            o[11]="Air "+Bits(s.E1,1024,s.Expansion)+"    Rough "+Bits(s.E1,2048,s.Expansion)+"    Cryo "+Bits(s.E1,4096,s.Expansion);
            o[12]="Filament off proof "+(s.Expansion?(On(s.E1,8192)?"YES":"NO"):"?")+"    Lab enable "+Bits(s.E1,16384,s.Expansion)+"    K1 "+Bits(s.E1,32768,s.Expansion);
            o[13]="ARM "+Bits(s.E1,64,s.Expansion)+"    Stop healthy "+Bits(s.E1,128,s.Expansion)+"    Pump "+Bits(s.E1,256,s.Expansion)+"    Vent "+Bits(s.E1,512,s.Expansion);
            o[14]="Ready "+State(On(s.Aux,1))+"    Moving "+State(On(s.Aux,2))+"    Fault "+State(On(s.Aux,4));
            o[15]="Buzzer "+State(On(s.Aux,8))+"    Filament OFF request "+State(On(s.Aux,16));
            o[16]="Seq "+s.Sequence+"    "+s.Uptime+" ms    I1..4 0x"+s.Base.ToString("X")+"    D1608E "+(s.Expansion?"ONLINE":"MISSING");
            o[17]=live ? "Local motion control / Ethernet monitoring" : "Simulated contacts and relay channels are independent";
        }
        return string.Join("|",o.Select(x=>x.Replace("|","/").Replace("\r"," ").Replace("\n"," ")));
    }
    public static int Main() {
        CultureInfo.CurrentCulture = Inv;
        try {
            var parts=Console.In.ReadToEnd().TrimEnd('\r','\n').Split('\t');
            if (parts.Length!=3 || parts[1].Length>64 || parts[2].Length>8192) throw new FormatException("Invalid panel input");
            Console.Write(Tick(Mask(parts[0],262143),parts[1],parts[2]));
            return 0;
        } catch(Exception e) { Console.Error.Write(e.Message); return 1; }
    }
}
