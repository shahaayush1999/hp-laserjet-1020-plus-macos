/* Function: 1000efd8 FUN_1000efd8 */


void FUN_1000efd8(int param_1)

{
  if (*(int *)(param_1 + 0x48) != 0) {
    FUN_1000efbc();
    *(undefined4 *)(param_1 + 0x48) = 0;
  }
  if (*(int *)(param_1 + 0x4c) != 0) {
    FUN_1000efbc();
    *(undefined4 *)(param_1 + 0x4c) = 0;
  }
  return;
}


