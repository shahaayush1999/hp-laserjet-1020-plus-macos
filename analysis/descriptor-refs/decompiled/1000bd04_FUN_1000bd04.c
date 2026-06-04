/* Function: 1000bd04 FUN_1000bd04 */


undefined4 FUN_1000bd04(undefined4 param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  undefined4 uVar4;
  char local_40 [16];
  undefined1 auStack_30 [48];
  
  iVar3 = FUN_100111b4(0x1d);
  FUN_1001b544(param_1,PTR_s_IN_TRAYS___100061a4);
  local_40[0] = (*(int *)(iVar3 + 0x38) == 1) + '0';
  local_40[1] = 0;
  FUN_1001b544(param_1,local_40);
  FUN_1001b544(param_1,PTR_s_ENUMERATED__100061a8);
  puVar1 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  if (*(int *)(iVar3 + 0x38) == 1) {
    if ((*(uint *)(iVar3 + 0x30) & 1) != 0) {
      FUN_1001b544(param_1,PTR_s_INTRAY1_PRIORITY_100061ac);
    }
    if ((*(uint *)(iVar3 + 0x30) & 2) != 0) {
      FUN_1001b544(param_1,PTR_s_INTRAY1_MP_100061b0);
    }
    FUN_1001b544(param_1,puVar1);
  }
  if (*(int *)(iVar3 + 0xa8) == 1) {
    FUN_1001b544(param_1,PTR_s_INTRAY2_PAPERTRAY_100061b4);
    FUN_1001b544(param_1,PTR_DAT_100060ec);
  }
  if (*(int *)(iVar3 + 0x118) == 1) {
    FUN_1001b544(param_1,PTR_s_INTRAY3_PAPERTRAY_100061b8);
    FUN_1001b544(param_1,PTR_DAT_100060ec);
  }
  FUN_100111d8(0x1d);
  FUN_1001b544(param_1,PTR_s_PAPERS__17_ENUMERATED__100061bc);
  puVar2 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  FUN_1000bad8(param_1);
  FUN_1001b544(param_1,PTR_s_LANGUAGES__3_ENUMERATED__100061c0);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061c4);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061c8);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_HTTP_100061cc);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_RESOLUTION__2_ENUMERATED__100061d0);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061d4);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061d8);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_BITSPERPIXEL__3_ENUMERATED__100061dc);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061e0);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061e4);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061e8);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_USTATUS__4_ENUMERATED__100061ec);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_DEVICE_100061f0);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_TIMED_100061f4);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_PAGE_100061f8);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_100061fc);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_MEMORY___10006200);
  puVar1 = PTR_DAT_10006090;
  uVar4 = FUN_100134fc();
  FUN_10007430(auStack_30,puVar1,uVar4);
  FUN_1001b544(param_1,auStack_30);
  FUN_1001b544(param_1,puVar2);
  return 1;
}


