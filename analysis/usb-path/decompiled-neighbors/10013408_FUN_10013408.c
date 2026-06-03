/*
Function: 10013408 FUN_10013408
Score: 18
*/


void FUN_10013408(uint *param_1)

{
  undefined *puVar1;
  undefined4 uVar2;
  uint *puVar3;
  uint uVar4;
  uint *puVar5;
  undefined1 in_b9;
  
  if (param_1 == (uint *)0x0) {
    return;
  }
  FUN_100181a4(DAT_100066ac,0xffffffff);
  puVar1 = PTR_DAT_100066a8;
  uVar4 = 0;
  puVar5 = param_1 + -2;
  puVar3 = param_1 + -3;
  while ((param_1 = param_1 + -1, *puVar3 != DAT_100066a4 || (!(bool)in_b9))) {
    puVar5 = puVar5 + -1;
    puVar3 = puVar3 + -1;
    uVar4 = uVar4 + 1;
    if (3 < uVar4) {
      FUN_10018214(DAT_100066ac);
      return;
    }
  }
  *param_1 = *param_1 & DAT_1000628c;
  uVar2 = DAT_100066ac;
  *(uint *)puVar1 = *(int *)puVar1 + *puVar5;
  FUN_10018214(uVar2);
  return;
}


