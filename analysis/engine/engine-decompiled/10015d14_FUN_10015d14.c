/* Function: 10015d14 FUN_10015d14 */


undefined4 FUN_10015d14(undefined4 param_1)

{
  undefined *puVar1;
  uint uVar2;
  uint uVar3;
  
  uVar2 = FUN_10015c68(1);
  puVar1 = PTR_DAT_10006920;
  if ((uVar2 & 0xffff) == DAT_100068e4) {
    return param_1;
  }
  if (((*(int *)(*(int *)(PTR_DAT_10006920 + 0x48) + 4) !=
        *(int *)(*(int *)(PTR_DAT_10006920 + 0x4c) + 4)) && ((uVar2 & DAT_10006930) == DAT_10005f5c)
      ) && (uVar3 = FUN_10015c68((DAT_10006934 |
                                 (uint)*(ushort *)(*(int *)(PTR_DAT_10006920 + 0x48) + 6) << 1) &
                                 0xffff), (DAT_10005e6c & uVar3) == 0)) {
    *(undefined4 *)(puVar1 + 0x4c) = *(undefined4 *)(puVar1 + 0x48);
  }
  if (((uint)(byte)PTR_DAT_10006920[0x59] << 0x18 != (uint)(byte)PTR_DAT_10006920[0x58] << 0x18) &&
     ((uVar2 & DAT_10006930) == DAT_10005f5c)) {
    FUN_10015c68((DAT_10006938 | ((int)((uint)(byte)PTR_DAT_10006920[0x59] << 0x18) >> 0x18) << 1) &
                 0xffff);
  }
  puVar1 = PTR_DAT_10006920;
  if (((*(int *)(PTR_DAT_10006920 + 0x54) != *(int *)(PTR_DAT_10006920 + 0x50)) &&
      ((uVar2 & DAT_10006930) == DAT_10005f5c)) &&
     (uVar2 = FUN_10015c68((DAT_1000693c | (uint)*(ushort *)(PTR_DAT_10006920 + 0x56) << 1) & 0xffff
                          ), (DAT_10005e6c & uVar2) == 0)) {
    *(undefined4 *)(puVar1 + 0x50) = *(undefined4 *)(puVar1 + 0x54);
  }
  return 1;
}


