<?xml version="1.0" encoding="UTF-8"?>
<Project Type="Project" LVVersion="25008000">
  <Property Name="NI.Project.Description" Type="Str">MAIZE vacuum operator console for Windows. Cryo and Turbo are the two gates with position switches.</Property>
  <Item Name="My Computer" Type="My Computer">
    <Property Name="server.tcp.enabled" Type="Bool">false</Property>
    <Item Name="MAIZE Vacuum Console.vi" Type="VI" URL="../MAIZE Vacuum Console.vi"/>
    <Item Name="MAIZE.Telemetry.exe" Type="Document" URL="../MAIZE.Telemetry.exe"/>
    <Item Name="Opta commissioning" Type="Folder">
      <Item Name="OptaTelemetry.ino" Type="Document" URL="../firmware/OptaTelemetry/OptaTelemetry.ino"/>
    </Item>
    <Item Name="Source and verification" Type="Folder">
      <Item Name="Telemetry.cs" Type="Document" URL="../Telemetry.cs"/>
      <Item Name="verify.py" Type="Document" URL="../verify.py"/>
      <Item Name="README.md" Type="Document" URL="../README.md"/>
    </Item>
    <Item Name="Dependencies" Type="Dependencies"/>
    <Item Name="Build Specifications" Type="Build"/>
  </Item>
</Project>
