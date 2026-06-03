/* Function: 10018fd4 hp1020_task_entry_10018fd4 */


void hp1020_task_entry_10018fd4(int param_1)

{
  undefined *puVar1;
  undefined4 uVar2;
  int iVar3;
  int *piVar4;
  undefined1 uVar5;
  
  uVar5 = 0;
  piVar4 = *(int **)(param_1 + 0x6c);
  uVar2 = rsil(1);
  if (((*(int *)(param_1 + 0x68) != 0) && (piVar4 != (int *)0x0)) && (*piVar4 == DAT_10006b10)) {
    *(undefined4 *)(param_1 + 0x68) = 0;
    if (param_1 == *(int *)(param_1 + 0x70)) {
      piVar4[9] = 0;
    }
    else {
      piVar4[9] = *(int *)(param_1 + 0x70);
      *(undefined4 *)(*(int *)(param_1 + 0x70) + 0x74) = *(undefined4 *)(param_1 + 0x74);
      *(undefined4 *)(*(int *)(param_1 + 0x74) + 0x70) = *(undefined4 *)(param_1 + 0x70);
    }
    piVar4[10] = piVar4[10] + -1;
    puVar1 = PTR_DAT_10006ac0;
    if (*(int *)(param_1 + 0x30) == 9) {
      iVar3 = *(int *)PTR_DAT_10006ac0;
      *(undefined4 *)(param_1 + 0x84) = 0x10;
      *(int *)puVar1 = iVar3 + 1;
      wsr(0,uVar2);
      rsync();
      uVar5 = 0;
      iVar3 = FUN_1001aac0(param_1);
      if (iVar3 == 0) {
        wsr(uVar5,uVar2);
        rsync();
      }
      else {
        FUN_10018750();
      }
      if (*(int *)(param_1 + 100) == 0) {
        *(undefined4 *)(param_1 + 0x4c) = 0;
      }
      else {
        FUN_1001bac4(param_1 + 0x4c);
      }
      uVar2 = rsil(1);
    }
  }
  wsr(uVar5,uVar2);
  rsync();
  return;
}


