/* Function: 1000f280 hp1020_work_mode_normalize_candidate */


void hp1020_work_mode_normalize_candidate(int param_1)

{
  if (*(short *)(param_1 + 10) == 0x200) {
    *(undefined2 *)(param_1 + 10) = 0x100;
  }
  return;
}
