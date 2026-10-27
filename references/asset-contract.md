# 素材与坐标契约

用于切图、进度条配对、Figma 拼装和开发交接。字段按任务需要填写，不为了完整模板虚构数据。

## 清单的最小信息

每个元素至少记录文件名、用途、源参考版本、导出像素尺寸、目标逻辑尺寸、透明要求、所属页面/角色/版本、应独立或合并的内容。紧裁资产另外记录裁切偏移；配对资产记录共同坐标系和填充方向。导入后记录实际 Figma 节点 ID。

示例（数值仅解释坐标关系）：

```json
{
  "reference": "approved-gameplay-v2.png",
  "source_canvas_px": [1920, 1080],
  "target_canvas": [1920, 1080],
  "assets": [
    {
      "name": "objective-frame",
      "file": "png/objective-frame@4x.png",
      "source_origin_px": [680, 85],
      "export_scale": 4,
      "crop_offset_export_px": [8, 4],
      "size_px": [1400, 108],
      "include": ["outer-frame", "stage-lines"],
      "exclude": ["editable-text", "fill"],
      "alpha": "transparent",
      "figma_node_id": null
    },
    {
      "name": "objective-fill-full",
      "file": "png/objective-fill-full@4x.png",
      "source_origin_px": [687, 91],
      "export_scale": 4,
      "crop_offset_export_px": [0, 0],
      "size_px": [1360, 68],
      "alpha": "solid-fill-is-allowed",
      "figma_node_id": null
    }
  ],
  "pairs": [
    {
      "frame": "objective-frame",
      "fill": "objective-fill-full",
      "fill_origin_in_frame": [5, 5],
      "growth_direction": "left-to-right",
      "clipping": "reveal-full-fill-under-frame"
    }
  ]
}
```

`source_origin_px` 为紧裁前元素在参考画布中的原点；`crop_offset_export_px` 为导出倍率下裁掉的左/上边距。上述示例在 1:1 还原时，最终位置为 `(682, 86)`，逻辑尺寸为 `350×27`。4 倍素材不是 4 倍大的 Figma 控件。

参考转到目标画布的变换若为 `(sx, sy, tx, ty)`：

```text
x = (sourceX + cropLeft / exportScale) * sx + tx
y = (sourceY + cropTop  / exportScale) * sy + ty
w = pngWidth  / exportScale * sx
h = pngHeight / exportScale * sy
```

等比例保留视觉时使用相同 sx/sy，加平移处理留白。参考和目标长宽比不同，应选定保比例、裁切或重排方案，不默认把整个界面非等比拉伸。图标、证件和头像特别检查原始宽高比。

## 透明、紧裁与配对的区别

- 有 alpha 通道不等于存在透明背景。异形图标/底板检查外部透明像素；紧裁后的矩形满格填充可以全不透明，渐隐面板也可能只有半透明像素，不能因此统一判废。
- alpha 有效边界用 `alpha > 0` 检查，保留低透明度边缘；不要用过高阈值削掉羽化/阴影。
- 紧裁表示有效边界等于整张图的边界矩形，不表示四个角都必须有色或必须透明。
- RGB 中的白/黑色不能直接作为透明判据；设计内可能本来就有这些颜色。
- 进度条外框与填充分开紧裁后，仍需通过偏移回到同一逻辑空间。不要仅因 PNG 尺寸不同就把两者缩成一样大。
- 一组按钮要求统一尺寸时，允许有公共留白；给出统一画布与有效边界。此时不加 `--tight`。
- “外框中间透明”和“只移除文字”是不同要求，按本次指示选择是否保留内底板。

## 检查脚本

依赖 Python 与 Pillow。先查可用运行时；Windows 可用工作区依赖工具返回的 Python。脚本只读素材，输出报告，不裁剪、不改原图。

```powershell
& $pythonExe $auditScript 'C:\UIWork\outputs\example\png' --tight --out 'C:\UIWork\outputs\example\png-audit.json'
```

`$pythonExe` 和 `$auditScript` 应为本机实际绝对路径；`$auditScript` 指向本技能的 `scripts/audit_png.py`。多个文件/目录可顺序传入；只有 `--recursive` 才扫描子目录。目录应指向生产切图目录，避免把不透明的展示拼图当透明素材验收。

异形素材可加 `--require-clear`，强制检查至少存在一个 alpha=0 像素；满格填充或只有半透明渐隐的矩形素材不加此选项。默认始终报告 alpha 极值及透明/半透明像素是否存在，由素材契约判断是否符合设计。

退出码 0 表示所查文件通过指定机械检查，1 表示发现格式/透明/边距或读取问题，2 表示未找到输入素材或参数错误。报告不能证明无烘焙文字、无伪棋盘残留、无边缘杂色，也不能证明与概念图相同；仍需查看素材和整屏合成。

## 实际显示检查

1. 素材叠在浅灰、深灰及游戏底图上，查看白边、黑边、透明孔洞及残留底色。
2. 外框与填充在 0%、50%、100% 各合成一次，检查原点、边框覆盖和阶段线层级。
3. 对比 PNG 有效边界、Figma 图片节点范围与实际渲染范围。位置看似正确但间距偏大时，先查透明边距和 FIT 留白。
4. 如需紧裁，先保存裁切偏移，再更新拼装位置和配对关系；保留原文件或另存版本。
