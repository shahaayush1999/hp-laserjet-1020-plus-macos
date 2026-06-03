/* Function: 100072b0 FUN_100072b0 */


void FUN_100072b0(int param_1,undefined4 param_2)

{
  undefined1 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined1 *puVar4;
  int iVar5;
  undefined4 uVar6;
  undefined1 *puVar7;
  undefined1 local_60 [32];
  undefined1 auStack_40 [64];
  
  FUN_1001b38c(auStack_40,PTR_s_0123456789ABCDEF_10005d64,0x11);
  puVar4 = local_60;
  do {
    puVar7 = puVar4;
    iVar5 = FUN_1001b6b0(param_1,param_2);
    *puVar7 = auStack_40[iVar5];
    param_1 = FUN_1001b668(param_1,param_2);
    puVar2 = PTR_DAT_10005d2c;
    puVar4 = puVar7 + 1;
  } while (param_1 != 0);
  puVar7[1] = 0;
  uVar6 = FUN_100169d4(local_60);
  puVar3 = PTR_DAT_10005d50;
  *(undefined4 *)puVar2 = uVar6;
  FUN_10007070(*(int *)puVar3 == 0);
  puVar2 = PTR_DAT_10005d34;
  if (local_60 <= puVar7) {
    do {
      uVar1 = *puVar7;
      puVar7 = puVar7 + -1;
      (**(code **)puVar2)(uVar1);
    } while (local_60 <= puVar7);
  }
  FUN_10007070(*(undefined4 *)PTR_DAT_10005d50);
  return;
}


