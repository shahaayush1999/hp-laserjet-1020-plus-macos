/* Function: 100136d8 hp1020_calibration_control_queue_worker_candidate */


void hp1020_calibration_control_queue_worker_candidate(void)

{
  undefined4 auStack_80 [3];
  undefined4 uStack_74;
  undefined1 auStack_70 [4];
  undefined4 uStack_6c;
  undefined4 uStack_68;
  undefined4 uStack_64;
  undefined4 uStack_60;
  undefined4 uStack_50;
  undefined4 uStack_4c;
  undefined4 uStack_48;
  undefined4 uStack_44;
  undefined4 uStack_30;
  
  FUN_1001214c();
  do {
    threadx_queue_receive_wait_candidate(PTR_DAT_100066f8,auStack_80,0xffffffff);
    switch(auStack_80[0]) {
    case 0x11:
    case 0x41:
      FUN_100126b0(0);
      break;
    case 0x40:
      FUN_10012644(0);
      uStack_6c = 7;
      uStack_60 = 4;
      uStack_64 = 1;
      uStack_68 = uStack_74;
      FUN_10010338(auStack_70,0);
      uStack_50 = 7;
      uStack_30 = 1;
      uStack_4c = 1;
      uStack_48 = 1;
      uStack_44 = 1;
      FUN_10010398(&uStack_50);
      FUN_100103f8();
      FUN_1001040c();
    }
  } while( true );
}


