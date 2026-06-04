/* Function: 10015df8 hp1020_engine_status_poll_candidate */


/* high confidence: Engine status polling path */

void hp1020_engine_status_poll_candidate(int param_1)

{
  bool bVar1;
  undefined *puVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  ushort uVar7;
  uint uVar6;
  bool bVar8;
  uint uVar9;
  undefined4 local_40;
  uint uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  int iStack_30;

  uVar9 = DAT_10005e34;
  iStack_30 = param_1;
  uVar4 = hp1020_engine_status_io_candidate(1);
  bVar1 = false;
  if ((uVar4 & 0xffff) != DAT_100068e4) {
    uVar6 = DAT_1000604c;
    if ((uVar4 & DAT_10006940) != DAT_10006940) {
      uVar5 = hp1020_engine_status_io_candidate(0x20);
      bVar1 = false;
      uVar6 = DAT_10006944;
      if (((DAT_10005ddc & uVar5) == 0) && (uVar6 = DAT_10006948, (uVar5 & 0x400) == 0)) {
        uVar5 = hp1020_engine_status_io_candidate(2);
        bVar1 = false;
        if ((uVar5 & 0x100) == 0) {
          if ((uVar5 & 0xc0) == 0) {
            uVar6 = DAT_1000696c;
            if ((((((DAT_10005f5c & uVar5) == 0) && (uVar6 = DAT_100063ec, (uVar5 & 0x424) == 0)) &&
                 (uVar6 = DAT_100063dc, (DAT_1000605c & uVar5) == 0)) &&
                (uVar6 = DAT_10006970, (DAT_10005dc8 & uVar5) == 0)) &&
               (((uVar4 & 0x40) == 0 || (uVar6 = uVar9, (uVar5 & 0x200) != 0)))) {
              bVar1 = true;
              uVar6 = DAT_10006958;
            }
          }
          else {
            uVar7 = hp1020_engine_status_io_candidate(0x16);
            uVar3 = DAT_1000696c;
            bVar1 = false;
            if (uVar7 == 0x40) {
              bVar1 = true;
              uVar6 = DAT_10006958;
            }
            else {
              uVar6 = DAT_1000695c;
              if ((((uVar7 & 0x10) == 0) && (uVar6 = DAT_10006960, (uVar7 & 8) == 0)) &&
                 (uVar6 = uVar9, (uVar7 & 4) != 0)) {
                uVar6 = DAT_10006964;
              }
            }
            if ((uVar7 & 0xfe) == 0) {
              hp1020_engine_status_io_candidate(DAT_10006968);
            }
            else if (((uVar7 & 0x40) != 0) && ((DAT_10005f5c & uVar5) != 0)) {
              hp1020_engine_status_io_candidate(DAT_10006968);
              uVar6 = uVar3;
            }
          }
        }
        else {
          uVar9 = hp1020_engine_status_io_candidate(0x13);
          switch(uVar9 >> 1 & 0x3f) {
          default:
            uVar6 = DAT_1000694c;
            break;
          case 0x10:
          case 0x14:
          case 0x18:
            uVar6 = DAT_10006950;
          }
          hp1020_engine_status_io_candidate(0x16);
          bVar1 = false;
        }
      }
    }
    bVar8 = false;
    if ((uVar6 & 0xffff) == DAT_10006974) {
      uVar6 = DAT_10006978;
    }
    if (*(uint *)(PTR_DAT_10006920 + 0x60) == uVar6) {
      if (iStack_30 == 1) {
        bVar8 = true;
      }
    }
    else {
      if (((*(uint *)(PTR_DAT_10006920 + 0x60) & 0xffff) == 0x100) &&
         ((uVar6 & 0xffff) == DAT_10006364)) {
        FUN_10015dd0(0);
        local_40 = 0x17;
        uStack_38 = 0;
        uStack_34 = 0;
        uStack_3c = DAT_10006958;
        hp1020_queue_send_candidate(1,&local_40);
      }
      uVar9 = *(uint *)(PTR_DAT_10006920 + 0x60) & DAT_1000696c;
      if ((uVar9 == DAT_1000696c) && ((uVar6 & uVar9) != uVar9)) {
        hp1020_engine_status_io_candidate(DAT_1000697c);
        FUN_10015dd0(1);
      }
      bVar8 = true;
      *(uint *)(PTR_DAT_10006920 + 0x60) = uVar6;
    }
    if (bVar8) {
      local_40 = 0x17;
      uStack_38 = 0;
      uStack_34 = 0;
      uStack_3c = uVar6;
      hp1020_queue_send_candidate(1,&local_40);
    }
    puVar2 = PTR_DAT_10006920;
    if (((*(int *)(PTR_DAT_10006920 + 0x38) != 0) && ((uVar4 & DAT_10006980) == 0)) &&
       ((DAT_10006980 & *(ushort *)(PTR_DAT_10006920 + 100)) != 0)) {
      *(undefined4 *)(PTR_DAT_10006920 + 0x38) = 0;
      *(undefined4 *)(puVar2 + 0x30) = 1;
      hp1020_video_reset_dispatch_candidate();
    }
    if (bVar1) {
      *(undefined4 *)(PTR_DAT_10006920 + 0x30) = 1;
    }
    puVar2 = PTR_DAT_10006920;
    if ((*(int *)(PTR_DAT_10006920 + 0x2c) != 0) && ((uVar4 & DAT_10005dc8) == 0)) {
      if ((uVar4 & 0x80) != 0) {
        *(undefined4 *)(PTR_DAT_10006920 + 0x3c) = 1;
      }
      *(undefined4 *)(puVar2 + 0x30) = 1;
      *(undefined4 *)(puVar2 + 0x2c) = 0;
    }
    if (((uVar4 & DAT_10006980) == 0) && (*(int *)(PTR_DAT_10006920 + 0x3c) != 0)) {
      *(undefined4 *)(PTR_DAT_10006920 + 0x3c) = 0;
    }
    puVar2 = PTR_DAT_10006920;
    *(uint *)(PTR_DAT_10006920 + 0x34) =
         (uint)((*(ushort *)(PTR_DAT_10006920 + 100) & DAT_10006980) != 0);
    *(short *)(puVar2 + 100) = (short)uVar4;
    return;
  }
  return;
}
