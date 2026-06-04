/* Function: 100104c8 hp1020_work_populate_from_page_params_candidate */


void hp1020_work_populate_from_page_params_candidate(undefined4 *param_1,undefined4 *param_2)

{
  *(undefined2 *)(param_1 + 3) = *(undefined2 *)((int)param_2 + 0x22);
  *(undefined2 *)((int)param_1 + 10) = *(undefined2 *)((int)param_2 + 10);
  *(undefined2 *)(param_1 + 4) = *(undefined2 *)((int)param_2 + 6);
  *(undefined2 *)((int)param_1 + 0x22) = *(undefined2 *)((int)param_2 + 0x12);
  *(undefined2 *)((int)param_1 + 0x1e) = *(undefined2 *)((int)param_2 + 0x16);
  *(undefined2 *)(param_1 + 5) = *(undefined2 *)((int)param_2 + 0x1a);
  *(undefined2 *)((int)param_1 + 0x16) = *(undefined2 *)((int)param_2 + 0x1e);
  *(undefined2 *)((int)param_1 + 0xe) = *(undefined2 *)((int)param_2 + 0xe);
  *param_1 = *param_2;
  return;
}
