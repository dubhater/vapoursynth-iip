Description
===========

Integrated Image Processor for VapourSynth. It performs motion-compensated temporal denoising, sharpening, and deringing, mostly on edges.

This is a port of the Avisynth function iip, version 0.5a.


Usage
=====
::

    iip(clp[, dest_x=None, dest_y=None, duststr=2, dustweight=1.0, ss1_x=1.414, ss1_y=1.414, detailcontr1=104, detailcontr2=208, contr_radius=2, PixSharp=0.4, ss2_x=3.5, ss2_y=3.5, Xstren=255, Xlimit=255, subpelstren=1.58, flatweight=0, antiflicker1=True, antiflicker2=True, protect_floor=0, protect_bias=16, dering=-80, dering_weight=1.0, dering_floor=8, dering_bias=16, detail_floor=20, EQ=2, exborder=False, warp_Y=False, warp_UV=False, debug="Mickey Mouse", cropx=40, cropy=20])


Parameters:
    *clp*
        A clip to process. It must be 8 bit, either GRAY or YUV.
        
    *dest_x*, *dest_y*
        Target resolution.
        
        Save a resize step when using supersampling.
        
        Default: same as the original resolution.
        
    *duststr*
        Limits how much the denoising is allowed to change the pixels.

        Default: 2.

    *dustweight*
        Weight of the denoised clip blended with the not denoised clip.

        Default: 1.0.

    *ss1_x*, *ss1_y*
        Supersampling ratio before first sharpening.
        
        Default: 1.414, 1.414.

    *detailcontr1*
        Strength of wide radius (*contr_radius*) UnsharpMask stage. 0 disables this stage.

        Default: 104.

    *detailcontr2*
        Strength of small radius (1) UnsharpMask stage. 0 disables this stage.

        Default: 208.

    *contr_radius*
        The radius of wide radius UnsharpMask stage.

        Default: 2.

    *PixSharp*
        Strength of Sharpen stage. 0 disables this stage.

        Default: 0.4.

    *ss2_x*, *ss2_y*
        Supersampling ratio before second sharpening.

        Default: 3.5.

    *Xstren*
        Strength of Xsharpen stage.

        Default: 255.

    *Xlimit*
        Threshold of Xsharpen stage.

        Default: 255.

    *subpelstren*
        Strength of Blur before luma warping and Xsharpen.

        Default: 1.58.

    *flatweight*
        Areas that aren't edges normally aren't sharpened. Making this greater than 0 can change that.
        
        Range: 0..255.

        Default: 0.

    *antiflicker1*
        If True, *clp* will be processed with TemporalSoften before any other processing.

        Default: True.

    *antiflicker2*
        If True, the luma will be processed with TemporalSoften before luma warping and Xsharpen.

        Default: True.

    *protect_floor*
        ???

        Default: 0.

    *protect_bias*
        ???

        Default: 16.

    *dering*
        Deringing of sharpened clip.
        
        A value of 0 disables deringing. A positive value selects the old deringing routine, which uses Unfilter. A negative value selects the new and improved deringing routine, which uses bicubic resizing. The deringing is stronger the farther from 0 this value gets, in either direction.

        Default: -80.

    *dering_weight*
        Controls how visible the mask is when the value of *debug* is "dering". It has no effect when *debug* has other values.

        Default: 1.0.

    *dering_floor*
        ???

        Default: 8.

    *dering_bias*
        ???

        Default: 16.

    *detail_floor*
        ???

        Default: 20.

    *EQ*
        Edge quality.
        
        * 0 = deactivated (not recommended)
        * 1 = standard
        * 2 = better and slower
        * 3 = best and slowest
        
        When using 2 or 3 it's a good idea to disable deringing by setting *dering* to 0.

        Default: 2.

    *exborder*
        Don't process the outermost 8 pixels of the image. Chroma warping is still done on the entire image if *warp_UV* is True.

        Default: False.

    *warp_Y*
        Also sharpen the luma with AWarpSharp2.

        Default: False.

    *warp_UV*
        Warp the chroma along luma edges. Often useful for sources where colors are bleeding. Not required for clean sources.

        Default: False.

    *debug*
        Debugging output. Possible values:
        
        * "dering", "protect", "detail": Show what parts of the image would be processed at various stages of the script.
        * "showall": Show all of the above plus the processed result in the same frame.
        * "compareH", "compareV": Show original clip and processed result stacked horizontally or vertically.
        
        Any other value disables the debugging output.
        
        If the input clip is GRAY the debugging output will be YUV444P8.

        Default: "Mickey Mouse".

    *cropx*
        Used only when *debug* is "compareH" or "showall". Crop some pixels from the left and right of each clip before stacking them.

        Default: 40.

    *cropy*
        Used only when *debug* is "compareV" or "showall". Crop some pixels from the top and bottom of each clip before stacking them.

        Default: 20.



Requirements
============

   * `muvsfunc          <https://github.com/WolframRhodium/muvsfunc>`_
   * `AWarpSharp2       <https://github.com/dubhater/vapoursynth-awarpsharp2>`_
   * `MVTools           <https://github.com/dubhater/vapoursynth-mvtools>`_
   * RemoveGrain (included with VapourSynth)
   * `TemporalSoften2   <https://github.com/dubhater/vapoursynth-temporalsoften2>`_


License
=======

???
