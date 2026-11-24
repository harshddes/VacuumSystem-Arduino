<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="26008000">
	<Property Name="NI.Project.Description" Type="Str">MAIZE vacuum rack. Local Opta control and live LabVIEW indications.</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Ethernet" Type="Folder">
			<Item Name="MAIZE.Telemetry.exe" Type="Document" URL="../MAIZE.Telemetry.exe"/>
			<Item Name="Opta.address" Type="Document" URL="../Opta.address"/>
			<Item Name="Telemetry.cs" Type="Document" URL="../Telemetry.cs"/>
		</Item>
		<Item Name="Opta controller" Type="Folder">
			<Item Name="Controller.h" Type="Document" URL="../firmware/OptaTelemetry/Controller.h"/>
			<Item Name="Installation.h" Type="Document" URL="../firmware/OptaTelemetry/Installation.h"/>
			<Item Name="OptaTelemetry.ino" Type="Document" URL="../firmware/OptaTelemetry/OptaTelemetry.ino"/>
			<Item Name="PermissionRules.h" Type="Document" URL="../firmware/OptaTelemetry/PermissionRules.h"/>
			<Item Name="UnoBench.h" Type="Document" URL="../firmware/OptaTelemetry/UnoBench.h"/>
		</Item>
		<Item Name="Panel logic" Type="Folder">
			<Item Name="Interlock messages.vi" Type="VI" URL="../Interlock messages.vi"/>
			<Item Name="Vacuum permissions.vi" Type="VI" URL="../Vacuum permissions.vi"/>
			<Item Name="Valve pilot lamp.vi" Type="VI" URL="../Valve pilot lamp.vi"/>
		</Item>
		<Item Name="MAIZE Vacuum Console.vi" Type="VI" URL="../MAIZE Vacuum Console.vi"/>
		<Item Name="README.md" Type="Document" URL="../README.md"/>
		<Item Name="Start-UnoBench.ps1" Type="Document" URL="../Start-UnoBench.ps1"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
