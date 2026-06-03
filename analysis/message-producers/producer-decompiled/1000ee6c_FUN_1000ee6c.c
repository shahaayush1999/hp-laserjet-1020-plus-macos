/* Function: 1000ee6c FUN_1000ee6c */


void FUN_1000ee6c(void)

{
  undefined *puVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int *piVar5;
  
  puVar1 = PTR_DAT_100062e8;
  for (piVar5 = *(int **)PTR_DAT_100062e4; piVar5 != (int *)0x0; piVar5 = (int *)*piVar5) {
    for (piVar4 = *(int **)(piVar5[3] + 0x70); piVar4 != (int *)0x0; piVar4 = (int *)*piVar4) {
      iVar3 = piVar4[3];
      iVar2 = *(int *)(iVar3 + 0x48);
      if (iVar2 != 0) {
        *(undefined2 *)(iVar2 + 0x48) = *(undefined2 *)(iVar2 + 0x4c);
      }
      iVar2 = *(int *)(iVar3 + 0x4c);
      if (((iVar2 != 0) && (*(short *)(iVar2 + 0x48) != *(short *)(iVar2 + 0xc))) &&
         (*(short *)puVar1 != 0)) {
        *(undefined2 *)(iVar2 + 0x48) = *(undefined2 *)(iVar2 + 0x4c);
      }
    }
  }
  return;
}


