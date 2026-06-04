/* Function: 10019ae8 FUN_10019ae8 */


undefined4 FUN_10019ae8(int param_1)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  int unaff_a10;
  undefined4 uVar4;
  uint uVar5;
  
  uVar5 = 0;
  uVar4 = rsil(1);
  iVar3 = 0;
  if (*(int *)(param_1 + 0x10) != 0) {
    *(undefined4 *)(param_1 + 0x10) = 0;
    *(undefined4 *)(param_1 + 0x14) = *(undefined4 *)(param_1 + 0xc);
    *(undefined4 *)(param_1 + 0x20) = *(undefined4 *)(param_1 + 0x18);
    iVar2 = *(int *)(param_1 + 0x2c);
    *(undefined4 *)(param_1 + 0x24) = *(undefined4 *)(param_1 + 0x18);
    if (iVar2 != 0) {
      *(undefined4 *)(param_1 + 0x2c) = 0;
      puVar1 = PTR_DAT_10006ac0;
      unaff_a10 = *(int *)(param_1 + 0x28);
      iVar3 = *(int *)PTR_DAT_10006ac0;
      *(undefined4 *)(param_1 + 0x28) = 0;
      *(int *)puVar1 = iVar3 + 1;
      iVar3 = iVar2;
    }
  }
  puVar1 = PTR_DAT_10006ac0;
  wsr(0,uVar4);
  rsync();
  if (iVar3 != 0) {
    do {
      uVar4 = rsil(1);
      iVar2 = *(int *)puVar1;
      *(undefined4 *)(unaff_a10 + 0x68) = 0;
      *(int *)puVar1 = iVar2 + 1;
      wsr((char)uVar5,uVar4);
      rsync();
      uVar5 = uVar5 & 0xffffcfff;
      FUN_1001bac4(unaff_a10 + 0x4c,uVar4);
      *(undefined4 *)(unaff_a10 + 0x4c) = 0;
      *(undefined4 *)(unaff_a10 + 0x84) = 0;
      unaff_a10 = *(int *)(unaff_a10 + 0x70);
      iVar3 = iVar3 + -1;
      uVar5 = uVar5 & 0xffffcfff;
      rtos_thread_ready_insert_candidate(*(undefined4 *)(unaff_a10 + 0x74));
    } while (iVar3 != 0);
    iVar2 = *(int *)PTR_DAT_10006a9c;
    iVar3 = *(int *)PTR_DAT_10006aa0;
    *(int *)PTR_DAT_10006ac0 = *(int *)PTR_DAT_10006ac0 + -1;
    if (iVar2 != iVar3) {
      FUN_10018750();
    }
  }
  return 0;
}


