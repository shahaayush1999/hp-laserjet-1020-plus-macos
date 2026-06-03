/* Function: 1000eff8 FUN_1000eff8 */


void FUN_1000eff8(void)

{
  int iVar1;
  int *piVar2;
  
  iVar1 = *(int *)PTR_DAT_100062e4;
  if (iVar1 != 0) {
    piVar2 = *(int **)(*(int *)(iVar1 + 0xc) + 0x70);
    while (piVar2 != (int *)0x0) {
      FUN_1000efd8(piVar2[3]);
      piVar2 = (int *)*piVar2;
      FUN_10013050(*(int *)(iVar1 + 0xc) + 0x70);
      FUN_10013408();
    }
    FUN_1000eeb8(*(undefined4 *)(iVar1 + 0xc));
    return;
  }
  return;
}


