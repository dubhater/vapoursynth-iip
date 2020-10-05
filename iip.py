from vapoursynth import core, GRAY, YUV, YUV444P8

import muvsfunc


def PixieDustApproximation(clip, limit=4):
    # Details guessed from Doom9 Dust thread: https://forum.doom9.org/showthread.php?t=42749
    # It's possible the convolution is meant to be applied before Degrain, not just before Analyse.
    prefilter = clip.std.Convolution(matrix=[1, 2, 1,
                                             2, 4, 2,
                                             1, 2, 1])
    
    super_for_analyse = prefilter.mv.Super()
    super_for_degrain = clip.mv.Super(levels=1)
    mvfw = super_for_analyse.mv.Analyse(isb=False)
    mvbw = super_for_analyse.mv.Analyse(isb=True)
    return clip.mv.Degrain1(super=super_for_degrain, mvbw=mvbw, mvfw=mvfw, limit=limit)


def YV12SubtractTol1WiderangeTrue(clip1, clip2):
    # YV12Subtract(clip1, clip2, tol=1, widerange=true)
    # result = (127.0 + (clip1 - clip2 < 0)) * ((clip1 - clip2) / 255.0) + 128.0;
    
    expressions = ["x y - 0 < 127 + x y - 255 / * 128 +"]
    
    if clip1.format.color_family != GRAY:
        expressions.append("")
    
    return core.std.Expr(clips=[clip1, clip2], expr=expressions)


def Xsharpen(clip, strength=128, threshold=8):
    """Ported by Myrsloik"""
    
    expressions = ['y x - x z - min {} < x z - y x - < z y ? {} * x {} * + x ?'
                   .format(threshold, strength / 256, (256 - strength) / 256)]
    
    if clip.format.color_family != GRAY:
        expressions.append("")
    
    return core.std.Expr(clips=[clip, clip.std.Maximum(planes=0), clip.std.Minimum(planes=0)], expr=expressions)
                         
                         
def FineEdge(clp, div):
    expressions = ["x y max"]
    
    if clp.format.color_family != GRAY:
        expressions.append("")
        
    return core.std.Expr(clips=[clp.std.Convolution(matrix=[ 5,  10,  5,
                                                             0,   0,  0,
                                                            -5, -10, -5], divisor=div, planes=0),
                                clp.std.Convolution(matrix=[ 5, 0,  -5,
                                                            10, 0, -10,
                                                             5, 0,  -5], divisor=div, planes=0)],
                         expr=expressions)
                                
                                
def Ylevels(clp, a, gamma, b, c, d):
    expressions = [f"x {a} - {b} {a} - / 1 {gamma} / pow {d} {c} - * {c} +"]
    
    if clp.format.color_family != GRAY:
        expressions.append("")
    
    return clp.std.Expr(expr=expressions)


def UnsharpMask(clip, strength=64, radius=3, threshold=8):
    """Ported by Myrsloik"""
    
    maxvalue = (1 << clip.format.bits_per_sample) - 1
    
    threshold = threshold * maxvalue // 255
    blurclip = clip.std.Convolution(matrix=[1] * (radius * 2 + 1), planes=0, mode='v')
    blurclip = blurclip.std.Convolution(matrix=[1] * (radius * 2 + 1), planes=0, mode='h')
    
    expressions = ['x y - abs {} > x y - {} * x + x ?'
                                            .format(threshold, strength / 128)]
                                            
    if clip.format.color_family != GRAY:
        expressions.append("")
        
    return core.std.Expr(clips=[clip, blurclip], expr=expressions)


def iip(clp, dest_x=None, dest_y=None, duststr=2, dustweight=1.0, ss1_x=1.414, ss1_y=1.414, detailcontr1=104, detailcontr2=208, contr_radius=2, PixSharp=0.4, ss2_x=3.5, ss2_y=3.5, Xstren=255, Xlimit=255, subpelstren=1.58, flatweight=0, antiflicker1=True, antiflicker2=True, protect_floor=0, protect_bias=16, dering=-80, dering_weight=1.0, dering_floor=8, dering_bias=16, detail_floor=20, EQ=2, exborder=False, warp_Y=False, warp_UV=False, debug="Mickey Mouse", cropx=40, cropy=20):

    ox = clp.width
    oy = clp.height
    
    if dest_x is None:
        dest_x = clp.width
    if dest_y is None:
        dest_y = clp.height
        
    if dering < 0:
        dering_floor *= 2
        
    if EQ > 3:
        EQ = 3
        
        
    if clp.format.bits_per_sample > 8:
        raise RuntimeError("iip: Only 8 bit clips are allowed.")
    
    if clp.format.color_family not in [GRAY, YUV]:
        raise RuntimeError("iip: Only GRAY and YUV clips are allowed.")
    
    if clp.format.color_family == GRAY:
        warp_UV = False
        
    
    cropx = int(cropx / 4) * 4
    cropy = int(cropy / 4) * 4
    xx_ss1 = int(ox * ss1_x / 16 + .5) * 16
    yy_ss1 = int(oy * ss1_y / 16 + .5) * 16
    xx_ss2 = int(ox * ss2_x / 16 + .5) * 16
    yy_ss2 = int(oy * ss2_y / 16 + .5) * 16
    xx_small = int(ox / (abs(dering) / 80 + 1.0) / 16 + .5) * 16 + 32
    yy_small = int(oy / (abs(dering) / 80 + 1.0) / 16 + .5) * 16 + 16
    
    if antiflicker1:
        clp = clp.focus2.TemporalSoften2(radius=2, luma_threshold=2, chroma_threshold=3, scenechange=23, mode=2)
        
    #---------------------------------------------------------------------------------------------------------------------
    # Base denoising by PixieDust
    #
    dusted = PixieDustApproximation(clp, limit=duststr)
    if dustweight == 0.0:
        dusted = clp
    elif dustweight < 1.0:
        dusted = core.std.Merge(clipa=clp, clipb=dusted, weight=dustweight)
        
    dustedgray = core.std.ShufflePlanes(clips=dusted, planes=0, colorfamily=GRAY)
    
    soft = dustedgray.resize.Bicubic(width=xx_small, height=yy_small, filter_param_a=0.2, filter_param_b=0.4).resize.Bicubic(width=xx_ss1, height=yy_ss1, filter_param_a=1.0, filter_param_b=0.0)
    
    #---------------------------------------------------------------------------------------------------------------------
    # Build EdgeMask to protect already sharp detail from oversharpening
    #
    last = core.std.MakeDiff(clipa=muvsfunc.Sharpen(clip=muvsfunc.Sharpen(clip=dustedgray, amountH=0.6), amountH=0.6),
                             clipb=muvsfunc.Blur(clip=muvsfunc.Blur(clip=dustedgray, amountH=1.0), amountH=1.0))
    
    edge00 = last.resize.Bicubic(width=xx_ss1, height=yy_ss1, filter_param_a=-1.0, filter_param_b=1.0)
    edge0 = muvsfunc.Blur(clip=edge00.std.Expr(expr=f"x 128 - abs {protect_floor} - {protect_bias} *").std.Deflate().std.Inflate(), amountH=1.58)
    edge00 = muvsfunc.Blur(clip=edge00.std.Expr(expr="x 128 - 2 *").std.Maximum(), amountH=1.58)
    # edge00 is not used past this point. Is there a typo? Where? -- dubhater
    
    #---------------------------------------------------------------------------------------------------------------------
    # Build DeRing'ing Mask: +++ OLD ROUTINE +++
    #
    if dering > 0:
        last = last.std.Maximum()
        
        edge1b = YV12SubtractTol1WiderangeTrue(clip1=muvsfunc.Blur(clip=last.std.Maximum(), amountH=1.58),
                                               clip2=last.std.Minimum())
        edge1b = edge1b.resize.Bicubic(width=xx_ss1, height=yy_ss1, filter_param_a=-1.0, filter_param_b=1.0).std.Expr(expr=f"x 128 - abs {dering_floor} - {dering_bias} *").std.Deflate()
        edge1b = muvsfunc.Blur(clip=edge1b, amountH=1.58)
    else:
        edge1b = last
        
    #---------------------------------------------------------------------------------------------------------------------
    # 1st supersampling stage to perform sharpening at
    #
    if ss1_x > 1.0 or ss1_y > 1.0:
        last = dustedgray.resize.Lanczos(width=xx_ss1, height=yy_ss1)
    else:
        last = dustedgray
        
    #---------------------------------------------------------------------------------------------------------------------
    # Build DeRing'ing Mask & perform dering'ing:   +++ NEW ROUTINE (Pre-processor) +++
    #
    if dering < 0:
        edge1b = YV12SubtractTol1WiderangeTrue(clip1=last, clip2=Xsharpen(clip=last, strength=256, threshold=255))
        # Here it multiplies by dering_floor, but in the old routine it subtracts dering_floor and multiplies by dering_bias. Is it a mistake? -- dubhater
        edge1b = edge1b.std.Expr(expr=f"x 128 - abs {dering_floor} *").std.Maximum().std.Inflate().std.Maximum().std.Inflate()
        edge1b = FineEdge(clp=edge1b, div=dering_bias)
        edge1b = muvsfunc.Blur(clip=edge1b, amountH=1.58)
        edge1b = Ylevels(clp=edge1b, a=19, gamma=1.6, b=208, c=0, d=255)
        last = core.std.MaskedMerge(clipa=last, clipb=soft, mask=edge1b)
        
    #-------- iterative sharpening, currently only 3-fold: its slow enough ... --------
    temp = last
    shrpcnt = 0
    mskcnt = 0
    if PixSharp != 0:
        shrpcnt += 1
    if detailcontr2 != 0:
        shrpcnt += 1
    if detailcontr1 != 0:
        shrpcnt += 1
        
    if EQ > shrpcnt:
        mskcnt = shrpcnt
    else:
        mskcnt = EQ
        
    # Stage 1 :  UnsharpMasking, wide radius -----------------------
    if detailcontr1 != 0:
        last = UnsharpMask(clip=last, strength=detailcontr1, radius=contr_radius, threshold=0)
        
        if shrpcnt == 1 or (mskcnt > 1 and shrpcnt >= mskcnt):
            if EQ > 0:
                last = core.std.MaskedMerge(clipa=last, clipb=temp, mask=edge0.std.Maximum().std.Inflate().std.Inflate())
            mskcnt -= 1
        
        shrpcnt -= 1
        
    # Stage 2 :  UnsharpMasking, small radius ----------------------
    if detailcontr2 != 0:
        last = UnsharpMask(clip=last, strength=detailcontr2, radius=1, threshold=0)
        
        if shrpcnt == 1 or (mskcnt > 1 and shrpcnt >= mskcnt):
            if EQ > 0:
                last = core.std.MaskedMerge(clipa=last, clipb=temp, mask=edge0.std.Inflate().std.Inflate())
            mskcnt -= 1
            
        shrpcnt -= 1
        
    # Stage 3 :  per-pixel sharpening ------------------------------
    if PixSharp != 0.0:
        last = muvsfunc.Sharpen(clip=last, amountH=PixSharp)
        
        if shrpcnt > 0 and EQ > 0:
            last = core.std.MaskedMerge(clipa=last, clipb=temp, mask=edge0)
            
    last = last.rgvs.RemoveGrain(mode=1)
    
    #---------------------------------------------------------------------------------------------------------------------
    # DeRing'ing of sharpen'ed clip: +++ OLD ROUTINE (Post-processor) +++
    #
    if dering > 0:
        # last = core.std.MaskedMerge(clipa=last, clipb=last.Unfilter(hsharp=-dering, vsharp=-dering), mask=edge1b.resize.Bicubic(width=xx_ss1, height=yy_ss1))
        raise RuntimeError("iip: dering > 0 is not implemented because Unfilter is not available.")
    
    if antiflicker2 == True:
        last = last.focus2.TemporalSoften2(radius=1, luma_threshold=2, chroma_threshold=3, scenechange=23, mode=2)
        
    #---------------------------------------------------------------------------------------------------------------------
    # 2nd supersampling stage to perform SubPel operation & XSharpening at
    #
    # Notes: Luma Warping  - may help for sources that are hard to get a "clean" picure from.
    #                      - Should help making the picture a little more "gracile" when doing DVD -> HDTV upsizing 
    if xx_ss2 != ox or yy_ss2 != oy:
        last = last.resize.Lanczos(width=xx_ss2, height=yy_ss2)
        
    if subpelstren != 0.0:
        last = muvsfunc.Blur(clip=last, amountH=subpelstren)
        
    if warp_Y:
        last = core.warp.AWarpSharp2(clip=last, thresh=0.5 * 256, depth=(ss2_x + ss2_y) / 2 * 3, blur=2, type=0)
        
    if Xstren != 0 and Xlimit != 0:
        last = Xsharpen(clip=last, strength=Xstren, threshold=Xlimit)
        
    last = last.resize.Lanczos(width=dest_x, height=dest_y).rgvs.RemoveGrain(mode=1)
    
    #---------------------------------------------------------------------------------------------------------------------
    # Build new EdgeMask of the enhanced clip
    #
    edge2 = last.resize.Bicubic(width=int(dest_x / 1.75 / 16 + 0.5) * 16, height=int(dest_y / 1.75 / 16 + 0.5) * 16, filter_param_a=1.0, filter_param_b=0.0)
    edge2 = edge2.std.Convolution(matrix=[-5, -7, -5,
                                          -7, 48, -7,
                                          -5, -7, -5], divisor=1)
    bordermask = core.std.BlankClip(clip=edge2, width=dest_x - 16, height=dest_y - 16, color=0xff)
    bordermask = bordermask.std.AddBorders(left=2, right=2, top=2, bottom=2, color=0x8f)
    bordermask = bordermask.std.AddBorders(left=2, right=2, top=2, bottom=2, color=0x6f)
    bordermask = bordermask.std.AddBorders(left=2, right=2, top=2, bottom=2, color=0x20)
    bordermask = bordermask.std.AddBorders(left=2, right=2, top=2, bottom=2, color=0x00)
    
    edge2 = edge2.std.Levels(min_in=detail_floor + int(detailcontr1 / 15 + detailcontr2 / 30 + PixSharp * 15), max_in=128, gamma=4.0, min_out=flatweight, max_out=255)
    edge2 = edge2.resize.Bicubic(width=dest_x, height=dest_y, filter_param_a=1.0, filter_param_b=0.0)
    if exborder:
        edge2 = core.std.Expr(clips=[edge2, bordermask], expr="x y min")
    edge2 = edge2.std.Inflate().std.Inflate()
    edge2 = muvsfunc.Blur(clip=edge2, amountH=1.58).std.Inflate().std.Inflate()
    edge2 = edge2.focus2.TemporalSoften2(radius=1, luma_threshold=63, chroma_threshold=63, scenechange=254, mode=2)
    
    #---------------------------------------------------------------------------------------------------------------------
    # Put original de-noised & not-sharpened clip into areas still appearing flat, after all that sharpening 
    #
    if dusted.format.num_planes > 1:
        blankchroma = core.std.BlankClip(clip=dusted, width=dest_x, height=dest_y)
        last = core.std.ShufflePlanes(clips=[last, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
    last = core.std.MaskedMerge(clipa=dusted.resize.Lanczos(width=dest_x, height=dest_y), clipb=last, mask=edge2, planes=0)
    
    #---------------------------------------------------------------------------------------------------------------------
    # Chroma Warping - often useful for sources where colors are "bleeding". Superfluid for clean sources.
    #
    if warp_UV:
        last = core.warp.AWarpSharp2(clip=last, thresh=0.5 * 256, depth=8.5 * (dest_x / ox + dest_y / oy), blur=2, type=0, chroma=0, planes=[1, 2])
        
    #---------------------------------------------------------------------------------------------------------------------
    # Visualizations
    #
    lastyuv = last
    clpyuv = clp
    if clp.format.num_planes == 1:
        blankchroma = core.std.BlankClip(clip=last, format=YUV444P8)
        lastyuv = core.std.ShufflePlanes(clips=[last, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
        blankchroma = core.std.BlankClip(clip=clp, format=YUV444P8)
        clpyuv = core.std.ShufflePlanes(clips=[clp, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
    
    greenblank = core.std.BlankClip(clip=lastyuv, color=[93, 74, 61])
    
    if debug == "dering":
        last = core.std.MaskedMerge(clipa=lastyuv, clipb=greenblank, mask=edge1b.resize.Bicubic(width=dest_x, height=dest_y).std.Expr(expr=f"x {dering_weight} *"))
    elif debug == "protect":
        last = core.std.MaskedMerge(clipa=lastyuv, clipb=greenblank, mask=edge0.resize.Bicubic(width=dest_x, height=dest_y).std.Expr(expr="x 0.75 *"))
    elif debug == "detail":
        last = core.std.MaskedMerge(clipa=lastyuv, clipb=greenblank, mask=edge2.resize.Bicubic(width=dest_x, height=dest_y).std.Expr(expr="x 0.75 *"))
    elif debug == "compareH":
        last = core.std.StackHorizontal(clips=[clpyuv.resize.Lanczos(width=dest_x, height=dest_y).std.Crop(left=cropx, right=cropx).std.AddBorders(right=4, color=[38, 106, 192]).text.Text(text="Original"),
                                               lastyuv.std.Crop(left=cropx, right=cropx).text.Text(text="iiP")])
    elif debug == "compareV":
        last = core.std.StackVertical(clips=[clpyuv.resize.Lanczos(width=dest_x, height=dest_y).std.Crop(top=cropy, bottom=cropy).std.AddBorders(bottom=4, color=[38, 106, 192]).text.Text(text="Original"),
                                             lastyuv.std.Crop(top=cropy, bottom=cropy).text.Text(text="iiP")])
    elif debug == "showall":
        lastshow = lastyuv.std.Crop(left=cropx, right=cropx, top=cropy, bottom=cropy).text.Text(text="iiP")
        edge0show = edge0.resize.Lanczos(width=dest_x, height=dest_y).std.Crop(left=cropx, right=cropx, top=cropy, bottom=cropy).text.Text(text="Protection of sharp edges")
        edge1bshow = edge1b.resize.Lanczos(width=dest_x, height=dest_y).std.Crop(left=cropx, right=cropx, top=cropy, bottom=cropy).text.Text(text="DeRing'ing")
        edge2show = edge2.resize.Lanczos(width=dest_x, height=dest_y).std.Crop(left=cropx, right=cropx, top=cropy, bottom=cropy).text.Text(text="Detail areas")
        
        blankchroma = core.std.BlankClip(clip=lastshow)
        
        edge0show = core.std.ShufflePlanes(clips=[edge0show, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
        edge1bshow = core.std.ShufflePlanes(clips=[edge1bshow, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
        edge2show = core.std.ShufflePlanes(clips=[edge2show, blankchroma], planes=[0, 1, 2], colorfamily=YUV)
        
        last = core.std.StackVertical(clips=[core.std.StackHorizontal(clips=[edge0show.std.AddBorders(right=4, bottom=4, color=[38, 106, 192]),
                                                                             edge1bshow.std.AddBorders(bottom=4, color=[38, 106, 192])]),
                                             core.std.StackHorizontal(clips=[edge2show.std.AddBorders(right=4, color=[38, 106, 192]),
                                                                             lastshow])])
        
    return last
