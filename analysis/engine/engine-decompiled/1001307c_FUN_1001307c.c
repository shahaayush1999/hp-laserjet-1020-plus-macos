/* Function: 1001307c FUN_1001307c */


undefined4 * FUN_1001307c(undefined4 *param_1)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  
  FUN_1001b770(1);
  puVar1 = (undefined4 *)*param_1;
  if (puVar1 == (undefined4 *)0x0) {
    puVar2 = (undefined4 *)0x0;
  }
  else {
    puVar2 = (undefined4 *)param_1[1];
    if (puVar1 == puVar2) {
      *param_1 = 0;
      param_1[1] = 0;
    }
    else {
      for (; (undefined4 *)*puVar1 != puVar2; puVar1 = (undefined4 *)*puVar1) {
      }
      puVar2 = (undefined4 *)*puVar1;
      *puVar1 = 0;
      param_1[1] = puVar1;
    }
  }
  FUN_1001b770();
  return puVar2;
}


