/* Function: 10013000 FUN_10013000 */


void FUN_10013000(int *param_1,undefined4 *param_2)

{
  FUN_1001b770(1);
  if (*param_1 == 0) {
    *param_1 = (int)param_2;
    param_1[1] = (int)param_2;
    *param_2 = 0;
    FUN_1001b770();
    return;
  }
  *(undefined4 **)param_1[1] = param_2;
  param_1[1] = (int)param_2;
  *param_2 = 0;
  FUN_1001b770();
  return;
}


