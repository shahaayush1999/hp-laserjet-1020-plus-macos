/* Function: 1000f280 FUN_1000f280 */


void FUN_1000f280(int param_1)

{
  if (*(short *)(param_1 + 10) == 0x200) {
    *(undefined2 *)(param_1 + 10) = 0x100;
  }
  return;
}


