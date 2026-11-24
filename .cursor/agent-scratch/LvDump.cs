using System;

class LvDump {
    static int Main(string[] args) {
        Type appType = Type.GetTypeFromProgID("LabVIEW.Application");
        if (appType == null) {
            Console.Error.WriteLine("NO_PROG_ID");
            return 2;
        }
        dynamic app = Activator.CreateInstance(appType);
        string viPath = args[0];
        string textPath = args[1];
        dynamic vi = app.GetVIReference(viPath);
        Console.WriteLine("NAME=" + vi.Name);
        Console.WriteLine("PATH=" + vi.Path);
        try {
            vi.PrintVIToText(textPath);
            Console.WriteLine("PRINTED");
        } catch (Exception e) {
            Console.WriteLine("PRINT_FAIL " + e.GetType().Name + " " + e.Message);
            if (e.InnerException != null) Console.WriteLine("INNER " + e.InnerException.Message);
        }
        try {
            object exported = vi.ExportVIStringsUTF8();
            Console.WriteLine("EXPORT=" + exported);
        } catch (Exception e) {
            Console.WriteLine("EXPORT_FAIL " + e.Message);
        }
        return 0;
    }
}
