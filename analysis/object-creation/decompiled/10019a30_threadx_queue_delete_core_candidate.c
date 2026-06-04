/* Function: 10019a30 threadx_queue_delete_core_candidate */


undefined4 threadx_queue_delete_core_candidate(undefined4 *param_1)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  undefined4 *puVar4;
  undefined4 uVar5;
  uint uVar6;
  undefined1 uVar7;
  
  puVar1 = PTR_DAT_10006b74;
  uVar6 = 0;
  uVar7 = 0;
  uVar5 = rsil(1);
  iVar2 = *(int *)PTR_DAT_10006b74;
  puVar4 = (undefined4 *)param_1[0xc];
  *param_1 = 0;
  *(int *)puVar1 = iVar2 + -1;
  puVar1 = PTR_DAT_10006b70;
  if (param_1 == puVar4) {
    *(undefined4 *)PTR_DAT_10006b70 = 0;
  }
  else {
    puVar4[0xd] = param_1[0xd];
    puVar4 = *(undefined4 **)puVar1;
    *(undefined4 *)(param_1[0xd] + 0x30) = param_1[0xc];
    if (puVar4 == param_1) {
      *(undefined4 *)puVar1 = param_1[0xc];
    }
  }
  puVar1 = PTR_DAT_10006ac0;
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + 1;
  wsr(0,uVar5);
  rsync();
  iVar3 = param_1[0xb];
  iVar2 = param_1[10];
  while (iVar3 != 0) {
    uVar5 = rsil(1);
    iVar3 = *(int *)puVar1;
    *(undefined4 *)(iVar2 + 0x68) = 0;
    *(int *)puVar1 = iVar3 + 1;
    wsr((char)uVar6,uVar5);
    rsync();
    uVar6 = uVar6 & 0xffffcfff;
    FUN_1001bac4(iVar2 + 0x4c,uVar5);
    *(undefined4 *)(iVar2 + 0x4c) = 0;
    *(undefined4 *)(iVar2 + 0x84) = 1;
    iVar2 = *(int *)(iVar2 + 0x70);
    uVar6 = uVar6 & 0xffffcfff;
    rtos_thread_ready_insert_candidate(*(undefined4 *)(iVar2 + 0x74));
    uVar7 = (undefined1)uVar6;
    iVar3 = param_1[0xb] + -1;
    param_1[0xb] = iVar3;
  }
  uVar5 = rsil(1);
  *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
  wsr(uVar7,uVar5);
  rsync();
  if (*(int *)PTR_DAT_10006a9c != *(int *)PTR_DAT_10006aa0) {
    FUN_10018750(*(int *)PTR_DAT_10006a9c,uVar5);
  }
  return 0;
}


