/* Function: 10010398 hp1020_child_page_record_create_candidate */


void hp1020_child_page_record_create_candidate(undefined4 *param_1)

{
  undefined4 *puVar1;
  int iVar2;
  undefined4 local_30 [3];
  undefined4 *puStack_24;

  puVar1 = (undefined4 *)FUN_10013140(0x50,1);
  FUN_1000f204();
  puVar1[0x13] = 0;
  puVar1[0x12] = 0;
  *puVar1 = *param_1;
  local_30[0] = 3;
  puStack_24 = puVar1;
  hp1020_queue_send_candidate(3,local_30);
  iVar2 = FUN_1000f228();
  FUN_100104c8(iVar2,param_1);
  *(undefined2 *)(iVar2 + 0x48) = 1;
  *(undefined2 *)(iVar2 + 0x4a) = 1;
  *(undefined1 *)(iVar2 + 0x76) = 0;
  local_30[0] = 5;
  puStack_24 = (undefined4 *)iVar2;
  hp1020_queue_send_candidate(3,local_30);
  return;
}
