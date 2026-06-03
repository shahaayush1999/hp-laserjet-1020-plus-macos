/* Function: 1000f030 FUN_1000f030 */


undefined4 FUN_1000f030(int param_1)

{
  if ((*(short *)(param_1 + 0x4a) != 1) && (*(short *)(param_1 + 0x72) != 1)) {
    FUN_1000ef74(param_1 + 0x50,*(undefined2 *)(param_1 + 0x4e));
    return 1;
  }
  FUN_1000f0a8(param_1 + 0x50,1);
  FUN_10013408(param_1);
  return 0;
}


