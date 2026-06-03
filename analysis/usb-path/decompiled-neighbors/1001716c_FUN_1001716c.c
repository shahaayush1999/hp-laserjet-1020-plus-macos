/*
Function: 1001716c FUN_1001716c
Score: 0
*/


undefined4 FUN_1001716c(int param_1,undefined4 param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  
  uVar2 = rsil(0xf);
  uVar1 = *(undefined4 *)(PTR_PTR_10006a60 + param_1 * 4);
  *(undefined4 *)(PTR_PTR_10006a60 + param_1 * 4) = param_2;
  wsr(0,uVar2);
  rsync();
  return uVar1;
}


