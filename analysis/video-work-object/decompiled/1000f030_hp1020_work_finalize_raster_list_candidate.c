/* Function: 1000f030 hp1020_work_finalize_raster_list_candidate */


undefined4 hp1020_work_finalize_raster_list_candidate(int param_1)

{
  if ((*(short *)(param_1 + 0x4a) != 1) && (*(short *)(param_1 + 0x72) != 1)) {
    FUN_1000ef74(param_1 + 0x50,*(undefined2 *)(param_1 + 0x4e));
    return 1;
  }
  hp1020_work_list_mark_or_send_candidate(param_1 + 0x50,1);
  FUN_10013408(param_1);
  return 0;
}
