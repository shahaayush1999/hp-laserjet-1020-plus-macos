/* Function: 1000b774 FUN_1000b774 */


void FUN_1000b774(undefined4 param_1,undefined4 param_2)

{
  undefined2 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  undefined4 uVar5;
  
  iVar4 = FUN_1000a2a4(param_2);
  puVar3 = PTR_s_USTATUS_100060e0;
  puVar2 = PTR_DAT_100060d4;
  if (iVar4 == 0) {
    return;
  }
  uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
  *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
  *(undefined2 *)(puVar2 + 4) = uVar1;
  FUN_1001b544(puVar2,puVar3);
  FUN_1001b544(puVar2,PTR_DAT_100060e4);
  FUN_1001b544(puVar2,PTR_s_TIMED_10006140);
  FUN_1001b544(puVar2,PTR_DAT_100060ec);
  iVar4 = FUN_100169d4(puVar2);
  FUN_1000b624(puVar2 + iVar4,param_2);
  FUN_1001b544(puVar2,PTR_DAT_100060f8);
  FUN_1000b1c4();
  iVar4 = FUN_100169d4(puVar2);
  uVar5 = FUN_1000dc00(iVar4 + 1);
  FUN_1001693c(uVar5,puVar2);
  FUN_1000b290(uVar5,1,param_1);
  return;
}


