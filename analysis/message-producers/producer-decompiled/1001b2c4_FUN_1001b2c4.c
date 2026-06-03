/* Function: 1001b2c4 FUN_1001b2c4 */


void FUN_1001b2c4(int param_1,int *param_2)

{
  *param_2 = param_1;
  param_2[1] = *(int *)(param_1 + 4);
  *(int **)(param_1 + 4) = param_2;
  *(int **)param_2[1] = param_2;
  return;
}


