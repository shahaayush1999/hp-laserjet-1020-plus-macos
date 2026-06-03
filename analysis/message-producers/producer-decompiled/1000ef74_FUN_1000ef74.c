/* Function: 1000ef74 FUN_1000ef74 */


void FUN_1000ef74(undefined4 *param_1,int param_2)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = (int *)*param_1;
  iVar2 = 1;
  if (param_2 != 0) {
    iVar2 = param_2;
  }
  for (; piVar1 != (int *)0x0; piVar1 = (int *)*piVar1) {
    *(short *)(piVar1[3] + 0x4e) = (short)iVar2;
  }
  return;
}


