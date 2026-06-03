/* Function: 100163b0 hp1020_engine_thread_candidate */


void hp1020_engine_thread_candidate(void)

{
  uint uVar1;
  undefined *puVar2;
  uint uVar3;
  int iVar4;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  
  puVar2 = PTR_DAT_10006920;
  *(undefined4 *)(PTR_DAT_10006920 + 0x68) = 0;
  FUN_1001215c(2);
  FUN_100160a8();
  uVar1 = DAT_10006420;
  *(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
  while (uVar3 = FUN_10015df8(0), (uVar3 & uVar1) == uVar1) {
    FUN_1001766c(1);
  }
  FUN_10016024();
  FUN_100165a4();
  FUN_10011258(0xf,PTR_FUN_100069b4);
  puVar2 = PTR_LAB_100069b8;
  FUN_10011258(0x10,PTR_LAB_100069b8);
  FUN_10011258(0x11,puVar2);
  FUN_10011258(0x12,puVar2);
  FUN_10011258(0x13,puVar2);
  FUN_10011258(0x14,puVar2);
  FUN_10016024();
  uStack_2c = 2;
  uStack_30 = 0x16;
  hp1020_queue_send_candidate(1,&uStack_30);
  FUN_10012184(2);
  puVar2 = PTR_DAT_10006920;
  iVar4 = *(int *)(PTR_DAT_10006920 + 0x24);
  while (iVar4 == 0) {
    iVar4 = threadx_queue_receive_wait_candidate(PTR_DAT_100069bc,&uStack_30,0x32);
    if (iVar4 == 0) {
      FUN_10016164(&uStack_30);
    }
    else {
      FUN_10015df8(0);
    }
    iVar4 = *(int *)(puVar2 + 0x24);
  }
  return;
}


