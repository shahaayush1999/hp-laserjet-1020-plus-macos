/* Function: 10015438 hp1020_video_alt_render_candidate */


undefined4 hp1020_video_alt_render_candidate(int param_1)

{
  undefined *puVar1;
  undefined4 uVar2;
  undefined4 uVar3;

  puVar1 = PTR_DAT_10006770;
  uVar2 = *(undefined4 *)(param_1 + 0x50);
  uVar3 = rsil(1);
  *(undefined4 *)(PTR_DAT_10006770 + 0x9c) = uVar2;
  *(undefined4 *)(puVar1 + 0xa0) = uVar2;
  wsr(0,uVar3);
  rsync();
  FUN_100140f8(uVar3);
  return 0;
}
