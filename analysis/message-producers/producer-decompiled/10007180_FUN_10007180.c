/* Function: 10007180 FUN_10007180 */


void FUN_10007180(int param_1)

{
  undefined1 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  undefined4 uVar5;
  undefined1 *puVar6;
  undefined1 *puVar7;
  undefined1 in_b2;
  undefined1 local_50 [32];
  undefined1 auStack_30 [48];
  
  FUN_1001b38c(auStack_30,PTR_s_0123456789_10005d60,0xb);
  puVar7 = local_50;
  if ((bool)in_b2) {
    param_1 = -param_1;
  }
  do {
    puVar6 = puVar7;
    iVar4 = FUN_1001b6b0(param_1,10);
    *puVar6 = auStack_30[iVar4];
    puVar7 = puVar6 + 1;
    param_1 = FUN_1001b668(param_1,10);
    puVar2 = PTR_DAT_10005d2c;
  } while (param_1 != 0);
  if ((bool)in_b2) {
    *puVar7 = 0x2d;
    puVar7 = puVar6 + 2;
  }
  *puVar7 = 0;
  uVar5 = FUN_100169d4(local_50);
  puVar3 = PTR_DAT_10005d50;
  *(undefined4 *)puVar2 = uVar5;
  puVar7 = puVar7 + -1;
  FUN_10007070(*(int *)puVar3 == 0);
  puVar2 = PTR_DAT_10005d34;
  if (local_50 <= puVar7) {
    do {
      uVar1 = *puVar7;
      puVar7 = puVar7 + -1;
      (**(code **)puVar2)(uVar1);
    } while (local_50 <= puVar7);
  }
  FUN_10007070(*(undefined4 *)PTR_DAT_10005d50);
  return;
}


