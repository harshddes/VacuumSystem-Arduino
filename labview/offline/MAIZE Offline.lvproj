<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="26008000">
	<Property Name="NI.Project.Description" Type="Str">MAIZE offline operator training and controller verification.</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Interlock messages.vi" Type="VI" URL="../../Interlock messages.vi"/>
		<Item Name="MAIZE Offline Console.vi" Type="VI" URL="../MAIZE Offline Console.vi"/>
		<Item Name="MAIZE.Offline.exe" Type="Document" URL="../MAIZE.Offline.exe"/>
		<Item Name="Offline valve lamp.vi" Type="VI" URL="../Offline valve lamp.vi"/>
		<Item Name="OfflineController.cpp" Type="Document" URL="../OfflineController.cpp"/>
		<Item Name="README.md" Type="Document" URL="../README.md"/>
		<Item Name="Vacuum permissions.vi" Type="VI" URL="../../Vacuum permissions.vi"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
