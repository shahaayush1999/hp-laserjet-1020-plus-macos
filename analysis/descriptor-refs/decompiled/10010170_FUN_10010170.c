/* Function: 10010170 FUN_10010170 */


void FUN_10010170(void)

{
  undefined4 local_50 [2];
  undefined4 uStack_48;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined4 uStack_30;
  undefined4 *puStack_2c;
  
  uStack_30 = 0x1f;
  puStack_2c = &uStack_40;
  FUN_10010f54(&uStack_30);
  uStack_40 = *(undefined4 *)(PTR_DAT_10006344 + 4);
  uStack_3c = *(undefined4 *)PTR_DAT_10006344;
  uStack_38 = *(undefined4 *)(PTR_DAT_10006344 + 8);
  if (*(int *)(PTR_DAT_10006344 + 0xc) - 1U < 7) {
                    /* WARNING: Could not recover jumptable at 0x100101a9. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (**(code **)(PTR_switchdataD_10004a00_100063a4 + (*(int *)(PTR_DAT_10006344 + 0xc) - 1U) * 4))()
    ;
    return;
  }
  uStack_34 = 0;
  FUN_10010fd0(&uStack_30);
  local_50[0] = 0x2c;
  uStack_48 = 1;
  FUN_10013658(10,local_50);
  return;
}


