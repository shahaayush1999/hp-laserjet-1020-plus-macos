/* Function: 10013050 FUN_10013050 */


int * FUN_10013050(int *param_1)

{
  int *piVar1;
  int iVar2;
  
  FUN_1001b770(1);
  piVar1 = (int *)*param_1;
  if (piVar1 == (int *)0x0) {
    FUN_1001b770();
    return (int *)0x0;
  }
  iVar2 = *piVar1;
  *param_1 = iVar2;
  if (iVar2 == 0) {
    param_1[1] = 0;
  }
  FUN_1001b770();
  return piVar1;
}


