// Shared with the Formula Node in Vacuum permissions.vi. All inputs are normalized.
// Valve bits: Roughing 1, Let-up 2, Turbo 4, Cryo 8. Position pairs in that order:
// 0 unknown/in transit, 1 closed, 2 open, 3 contradictory.
// 'attempt' is the selected request before protective arbitration.
alarms = 0;
if ((status & 1) == 0) alarms |= 1;
if ((status & 2) == 0) alarms |= 2;
if ((status & 4) == 0) alarms |= 4;
if ((status & 8) == 0) alarms |= 8;
if ((status & 16) == 0) alarms |= 16;
if ((status & 32) != 0) alarms |= 32;
if ((pos & 192) == 192) alarms |= 64;
if ((pos & 48) == 48) alarms |= 128;
if ((pos & 192) == 0 && (events & 1) == 0) alarms |= 256;
if ((pos & 48) == 0 && (events & 2) == 0) alarms |= 512;
if ((events & 4) != 0) alarms |= 1024;
if ((events & 8) != 0) alarms |= 2048;
if ((site & 1) == 0) alarms |= 4096;
if ((attempt & 2) && (attempt & 13)) alarms |= 8192;
if (((attempt & 13) || (pos & 3) == 2 || (pos & 48) == 32 || (pos & 192) == 128)
    && ((pos & 12) != 4 || (site & 2) == 0)) alarms |= 16384;
if (((attempt & 2) || (pos & 12) == 8)
    && ((pos & 243) != 81 || (site & 4) == 0)) alarms |= 32768;
if (((attempt & 2) || (pos & 12) == 8) && (status & 64) == 0) alarms |= 65536;
if (((attempt & 1) || (pos & 3) == 2) && (status & 128) == 0) alarms |= 131072;
if (((attempt & 8) || (pos & 192) == 128) && (status & 256) == 0) alarms |= 262144;
if (((attempt & 4) || (pos & 48) == 32) && (status & 512) == 0) alarms |= 524288;
if (((attempt & 4) || (pos & 48) == 32) && (status & 1024) == 0) alarms |= 1048576;
if (((attempt & 12) || (pos & 48) == 32 || (pos & 192) == 128)
    && (status & 2048) == 0) alarms |= 2097152;
if (((attempt & 8) || (pos & 192) == 128) && (status & 4096) == 0) alarms |= 4194304;
if (((attempt & 4) || (pos & 48) == 32) && (status & 8192) == 0) alarms |= 8388608;
if ((site & 8) == 0 && (attempt & 13)) alarms |= 16777216;
if ((events & 16) != 0) alarms |= 33554432;
if ((events & 32) != 0) alarms |= 67108864;
if ((events & 64) != 0) alarms |= 134217728;
if (((attempt & 2) || (pos & 12) == 8) && (site & 16) == 0) alarms |= 268435456;
if ((events & 128) != 0) alarms |= 536870912;
if ((events & 256) != 0) alarms |= 1073741824;
