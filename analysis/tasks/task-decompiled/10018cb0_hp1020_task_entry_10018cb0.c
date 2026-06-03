/* Function: 10018cb0 hp1020_task_entry_10018cb0 */


void hp1020_task_entry_10018cb0(int param_1)

{
  undefined *puVar1;
  int iVar2;
  int *piVar3;
  undefined4 uVar4;
  undefined1 uVar5;
  
  uVar5 = 0;
  piVar3 = *(int **)(param_1 + 0x6c);
  uVar4 = rsil(1);
  if (((*(int *)(param_1 + 0x68) != 0) && (piVar3 != (int *)0x0)) && (*piVar3 == DAT_10006b0c)) {
    *(undefined4 *)(param_1 + 0x68) = 0;
    if (param_1 == *(int *)(param_1 + 0x70)) {
      piVar3[8] = 0;
    }
    else {
      piVar3[8] = *(int *)(param_1 + 0x70);
      *(undefined4 *)(*(int *)(param_1 + 0x70) + 0x74) = *(undefined4 *)(param_1 + 0x74);
      *(undefined4 *)(*(int *)(param_1 + 0x74) + 0x70) = *(undefined4 *)(param_1 + 0x70);
    }
    piVar3[9] = piVar3[9] + -1;
    puVar1 = PTR_DAT_10006ac0;
    if (*(int *)(param_1 + 0x30) == 8) {
      iVar2 = *(int *)PTR_DAT_10006ac0;
      *(undefined4 *)(param_1 + 0x84) = 0x10;
      *(int *)puVar1 = iVar2 + 1;
      wsr(0,uVar4);
      rsync();
      uVar5 = 0;
      iVar2 = FUN_1001aac0(param_1,uVar4);
      if (iVar2 != 0) {
        FUN_10018750();
      }
    }
    else {
      wsr(0,uVar4);
      rsync();
      uVar5 = 0;
    }
    if (*(int *)(param_1 + 100) == 0) {
      *(undefined4 *)(param_1 + 0x4c) = 0;
    }
    else {
      FUN_1001bac4(param_1 + 0x4c);
    }
    uVar4 = rsil(1);
  }
  wsr(uVar5,uVar4);
  rsync();
  return;
}


