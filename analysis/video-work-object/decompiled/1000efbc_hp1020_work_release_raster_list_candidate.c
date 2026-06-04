/* Function: 1000efbc hp1020_work_release_raster_list_candidate */


void hp1020_work_release_raster_list_candidate(int param_1)

{
  hp1020_work_list_mark_or_send_candidate(param_1 + 0x50,1);
  FUN_10013408(param_1);
  return;
}
