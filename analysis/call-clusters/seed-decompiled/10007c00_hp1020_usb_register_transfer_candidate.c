/* Function: 10007c00 hp1020_usb_register_transfer_candidate */


undefined4 hp1020_usb_register_transfer_candidate(int *param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined4 uVar4;
  int iVar5;
  int *piVar6;
  int iVar7;
  int iVar8;
  
  puVar3 = PTR_DAT_10005da0;
  puVar2 = PTR_DAT_10005d9c;
  puVar1 = PTR_DAT_10005d98;
  uVar4 = *(undefined4 *)PTR_DAT_10005d98;
  FUN_10008034(PTR_DAT_10005da0 + *(int *)PTR_DAT_10005d9c * 0x58,0,0);
  iVar8 = *(int *)puVar2;
  piVar6 = (int *)(puVar3 + iVar8 * 0x58);
  piVar6[1] = param_1[2];
  piVar6[2] = param_1[3];
  iVar7 = *(int *)puVar1;
  piVar6[6] = param_1[4];
  *piVar6 = iVar7;
  piVar6[0xe] = param_1[1];
  iVar5 = *param_1;
  *(int *)puVar2 = iVar8 + 1;
  piVar6[0xb] = iVar5;
  iVar5 = param_1[5];
  *(int *)puVar1 = iVar7 << 1;
  piVar6[0x15] = iVar5;
  piVar6[0x14] = 0;
  piVar6[0xf] = 0;
  return uVar4;
}


