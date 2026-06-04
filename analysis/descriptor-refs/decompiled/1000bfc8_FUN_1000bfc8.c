/* Function: 1000bfc8 FUN_1000bfc8 */


undefined4 FUN_1000bfc8(undefined4 param_1)

{
  uint uVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined *puVar4;
  undefined1 auStack_30 [48];
  
  FUN_1001b544(param_1,PTR_DAT_10006204);
  puVar3 = PTR_DAT_1000620c;
  if ((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) & 0x20000000) == 0) {
    puVar3 = PTR_DAT_10006208;
  }
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,PTR_s__2_ENUMERATED__10006210);
  puVar3 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  puVar2 = PTR_DAT_1000615c;
  FUN_1001b544(param_1,PTR_DAT_1000615c);
  puVar4 = PTR_DAT_1000620c;
  FUN_1001b544(param_1,PTR_DAT_1000620c);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  puVar2 = PTR_DAT_10006208;
  FUN_1001b544(param_1,PTR_DAT_10006208);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,PTR_s_PAGE__10006214);
  if ((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) & 0x10000000) == 0) {
    puVar4 = puVar2;
  }
  FUN_1001b544(param_1,puVar4);
  FUN_1001b544(param_1,PTR_s__2_ENUMERATED__10006210);
  puVar3 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  puVar2 = PTR_DAT_1000615c;
  FUN_1001b544(param_1,PTR_DAT_1000615c);
  puVar4 = PTR_DAT_1000620c;
  FUN_1001b544(param_1,PTR_DAT_1000620c);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  puVar2 = PTR_DAT_10006208;
  FUN_1001b544(param_1,PTR_DAT_10006208);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,PTR_s_DEVICE__10006218);
  uVar1 = *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x1e;
  if (uVar1 != 1) {
    if (uVar1 < 2) {
      puVar4 = puVar2;
      if (uVar1 != 0) goto LAB_1000c127;
    }
    else {
      puVar4 = PTR_s_VERBOSE_1000621c;
      if (uVar1 != 2) goto LAB_1000c127;
    }
  }
  FUN_1001b544(param_1,puVar4);
LAB_1000c127:
  FUN_1001b544(param_1,PTR_s__3_ENUMERATED__10006220);
  puVar3 = PTR_DAT_100060ec;
  FUN_1001b544(param_1,PTR_DAT_100060ec);
  puVar2 = PTR_DAT_1000615c;
  FUN_1001b544(param_1,PTR_DAT_1000615c);
  FUN_1001b544(param_1,PTR_DAT_1000620c);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_s_VERBOSE_1000621c);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_10006208);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,PTR_s_TIMED__10006224);
  FUN_10007430(auStack_30,PTR_DAT_10006228,
               *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x13 & 0x1ff);
  FUN_1001b544(param_1,auStack_30);
  FUN_1001b544(param_1,PTR_s__2_RANGE__1000622c);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_10006230);
  FUN_1001b544(param_1,puVar3);
  FUN_1001b544(param_1,puVar2);
  FUN_1001b544(param_1,PTR_DAT_10006234);
  FUN_1001b544(param_1,puVar3);
  return 1;
}


