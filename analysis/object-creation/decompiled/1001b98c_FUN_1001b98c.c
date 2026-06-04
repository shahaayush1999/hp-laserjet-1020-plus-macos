/* Function: 1001b98c FUN_1001b98c */


undefined4
FUN_1001b98c(int param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4,
            undefined4 *param_5,undefined4 *param_6,undefined4 *param_7)

{
  undefined4 uVar1;
  
  uVar1 = rsil(1);
  *param_2 = *(undefined4 *)(param_1 + 4);
  *param_3 = *(undefined4 *)(param_1 + 0x10);
  *param_4 = *(undefined4 *)(param_1 + 0x14);
  *param_5 = *(undefined4 *)(param_1 + 0x28);
  *param_6 = *(undefined4 *)(param_1 + 0x2c);
  *param_7 = *(undefined4 *)(param_1 + 0x30);
  wsr(0,uVar1);
  rsync();
  return 0;
}


