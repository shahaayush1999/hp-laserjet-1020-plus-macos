/* Function: 1001146c hp1020_data_store_thread_candidate */


void hp1020_data_store_thread_candidate(void)

{
  undefined2 *puVar1;
  undefined4 *puVar2;
  ushort *puVar3;
  byte *pbVar4;
  undefined *puVar5;
  byte *pbVar6;
  uint uStack_30;
  uint uStack_2c;
  uint uStack_28;
  uint *puStack_24;
  
  FUN_1001214c();
  puStack_24 = &uStack_2c;
  do {
    uStack_30 = 0;
    threadx_queue_receive_candidate(PTR_DAT_1000646c,3,1,&uStack_30,0xffffffff);
    threadx_queue_receive_candidate(PTR_DAT_1000646c,4,0,puStack_24,0xffffffff);
    uStack_30 = uStack_30 | uStack_2c;
    threadx_queue_receive_candidate(PTR_DAT_1000646c,3,1,puStack_24,0);
    uStack_30 = uStack_30 | uStack_2c;
    if ((uStack_30 & 2) != 0) {
      FUN_1001223c();
      FUN_1001766c(500);
      FUN_10012644(0);
    }
    puVar5 = PTR_DAT_1000647c;
    uStack_28 = 0;
    puVar1 = (undefined2 *)(PTR_DAT_1000647c + 0x10);
    puVar2 = (undefined4 *)(PTR_DAT_1000647c + 4);
    puVar3 = (ushort *)(PTR_DAT_1000647c + 0xe);
    pbVar4 = PTR_DAT_1000647c + 0xc;
    pbVar6 = PTR_DAT_1000647c + 0xd;
    FUN_10017e64(PTR_DAT_10006474,0xffffffff);
    do {
      if ((int)(*pbVar4 - 1) < (int)(uint)*pbVar6) {
        FUN_100115d0(puVar5);
        FUN_1001b38c(PTR_DAT_1000648c + *puVar3,*puVar2,*puVar1);
        *pbVar6 = 0;
      }
      puVar1 = puVar1 + 0xc;
      puVar2 = puVar2 + 6;
      puVar3 = puVar3 + 0xc;
      pbVar4 = pbVar4 + 0x18;
      pbVar6 = pbVar6 + 0x18;
      puVar5 = puVar5 + 0x18;
      uStack_28 = uStack_28 + 1;
    } while (uStack_28 < 0x16);
    FUN_1001161c();
    puVar5 = PTR_DAT_1000647c;
    if ((uStack_30 & 2) != 0) {
      **(undefined1 **)(PTR_DAT_1000647c + 4) = 0;
      FUN_100115d0(puVar5);
      FUN_100121e4();
    }
    FUN_10017ed8(PTR_DAT_10006474);
  } while( true );
}


