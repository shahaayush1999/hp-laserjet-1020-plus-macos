/* Function: 1000b624 FUN_1000b624 */


void FUN_1000b624(int param_1,undefined4 param_2)

{
  undefined4 uVar1;
  int iVar2;
  char cVar3;
  undefined *puVar4;
  
  FUN_1001b544(param_1,PTR_s_CODE__10006128);
  uVar1 = FUN_1000a2a4(param_2);
  iVar2 = FUN_100169d4(param_1);
  FUN_10007430(param_1 + iVar2,PTR_DAT_10006090,uVar1);
  puVar4 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  FUN_1001b544(param_1,PTR_s_DISPLAY___1000612c);
  uVar1 = FUN_100111b4(0x1a);
  FUN_1001b544(param_1,uVar1);
  FUN_1001b544(param_1,PTR_DAT_10006130);
  FUN_1001b544(param_1,puVar4);
  FUN_100111d8(0x1a);
  FUN_1001b544(param_1,PTR_s_ONLINE__10006134);
  cVar3 = FUN_10011178(0x18);
  puVar4 = DAT_1000613c;
  if (cVar3 == '\0') {
    puVar4 = PTR_s_FALSE_10006138;
  }
  FUN_1001b544(param_1,puVar4);
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  return;
}


