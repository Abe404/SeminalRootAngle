"""
Extract primary root angles for a folder of root images.
This script requires that the seed location segmentation and
root segmentations already exist.
"""

# Although pylint can be a little strict, it's still worth using it
# to check for basic errors
# Catching too general exception Exception (broad-except)
# pylint: disable=W0703
# Variable name "im" doesn't conform to snake_case naming style (invalid-name)
# pylint: disable=C0103
# pylint: disable=R0913 # Too many arguments (6/5) (too-many-arguments)
# pylint: disable=R0914 # Too many local variables (20/15) (too-many-locals)
# Too many positional arguments for function call (too-many-function-args)
# pylint: disable=E1121
# pylint: disable=R0915 # Too many statements (64/50) (too-many-statements)

import os
import time
import datetime

import numpy as np
from skimage.measure import label, regionprops
from skimage.morphology import skeletonize, remove_small_objects, binary_dilation
from skimage.io import imread, imsave
from skimage.draw import disk
from skimage.draw import line_aa
from skimage.draw import circle_perimeter
from skimage.color import gray2rgb
from skimage.transform import resize
from skimage import img_as_ubyte
from PIL import Image, ImageFont, ImageDraw
import humanize
from matplotlib import font_manager

def save(impath, im):

    im = im.astype(np.uint8)
    # what a hassle. why do we have to do this crap?
    new_p = Image.fromarray(im)
    if new_p.mode != 'RGB':
        new_p = new_p.convert('RGB')
    imsave(impath, np.array(new_p))

def load_seed_points(seg_im, max_seed_points):
    """ extract seed point centroids for seed point segmentations """
    # restrict to largest regions
    label_img = label(seg_im)
    def pixelcount(regionmask):
        return np.sum(regionmask)

    props = regionprops(label_img, extra_properties=(pixelcount,))
    centroids = []
    seed_masks = []
    pixel_counts = []
    for prop in props:
        if prop.pixelcount > 100:
            # row, col
            # y, x
            ys = [c[0] for c in prop.coords]
            xs = [c[1] for c in prop.coords]
            min_y = np.min(ys)
            xs_at_min_y = []
            for x, y in zip(xs, ys):
                if y == min_y:
                    xs_at_min_y.append(x)
            x = np.mean(xs_at_min_y)
            y = min_y / label_img.shape[0]
            x = x / label_img.shape[1]
            centroids.append([y, x])
            seed_mask = np.array(seg_im)
            seed_mask[label_img != prop.label] = 0
            seed_masks.append(seed_mask)
            pixel_counts.append(prop.pixelcount)
    if len(pixel_counts) > 0:
        pixel_counts, centroids, seed_masks = zip(*sorted(zip(pixel_counts,
                                                              centroids,
                                                              seed_masks),
                                                          reverse=True))
    # limit to max_seed_points_per_im biggest (max)
    return (centroids[:max_seed_points],
            seed_masks[:max_seed_points],
            pixel_counts[:max_seed_points])


def fix_first_row_im(debug_im):
    new_w = 640
    new_h = round(debug_im.shape[0] * (640 / debug_im.shape[1]))
    _t = time.time()
    assert np.max(debug_im) <= 1.0, 'expected float input'
    debug_im = (debug_im * 255).astype(np.uint8)
    debug_im = Image.fromarray(debug_im)
    #debug_im = np.array(debug_im.resize((new_w, new_h), PIL.Image.NEAREST))
    debug_im = np.array(debug_im.resize((new_w, new_h)))
    #print('resize time', time.time() - t)
    debug_im = debug_im[:640, :640]
    # make sure debug im is at least 640        
    zero_im = np.zeros((640, 640, 3))
    zero_im[:debug_im.shape[0], :debug_im.shape[1]] = debug_im
    debug_im = zero_im
    return debug_im


def get_merged_debug_im(debug_ims):
    """ convert debug images to one image.
        assumes first 4 could be any size and last 4
        are 640x640x3 """
    try:
        to_add = 8 - len(debug_ims)
        # add some empty images so this can still be used for incomplete i.e failed pipelines.
        for _ in range(to_add):
            debug_ims.append(np.zeros((640, 640, 3)))

        if to_add > 0:
            print('adding', to_add, 'debug_ims len is now', len(debug_ims))

        def fixim(im):
            im = im[:640, :640]
            # make sure debug im is at least 640        
            zero_im = np.zeros((640, 640, 3))
            zero_im[:im.shape[0], :im.shape[1]] = im
            zero_im = img_as_ubyte(zero_im)
            return zero_im
        
        merge1 = np.hstack((debug_ims[0], debug_ims[1], debug_ims[2], debug_ims[3]))
        merge2 = np.hstack((fixim(debug_ims[4]),fixim(debug_ims[5]),
                            fixim(debug_ims[6]),fixim(debug_ims[7])))

        merged = np.concatenate((merge1, merge2))
        print('merged min', np.min(merged), 'max', np.max(merged), 'dtype', merged.dtype)

        save('merged.png', merged)
        return merged
    except Exception as e:
        print('Exception creating image', e)
        raise e

def get_primary_root_angle(seed_centroid, inner_radius, outer_radius,
                           im, seg_im, seed_im, skel, save_debug_image):
    """ get the primary root angle for the specific seed centroid
        TODO: refactor this function. It's way too long.
    """

    # dont modify in place.. it gets messy so make a copy.
    _t = time.time()
    seg_im = np.array(seg_im)
    seed_im = np.array(seed_im)

    skel = np.array(skel)
    im = np.array(im).astype(float)
    im /= np.max(im)
    mask = np.zeros(skel.shape)

    debug_ims = []
    if save_debug_image:
        debug_ims.append(fix_first_row_im(gray2rgb(seg_im)))
        debug_ims.append(fix_first_row_im(gray2rgb(seed_im)))

    y = round(seed_centroid[0] * seed_im.shape[0])
    x = round(seed_centroid[1] * seed_im.shape[1])

    if save_debug_image:
        rgbskel = gray2rgb(skel)
        # add semi-circle to show location on skel
        rr, cc  = circle_perimeter(y, x, outer_radius)
        rr = [r if r > y else y for r in rr] # semi circle will be used.
        # make sure they are inside the image to avoid an error.
        rr = [min(max(r, 0), im.shape[0]-1) for r in rr]
        cc = [min(max(c, 0), im.shape[1]-1) for c in cc]
        rgbskel = rgbskel.astype(np.uint)
        rgbskel[rr, cc, 0] = 1.0
        rgbskel = fix_first_row_im(rgbskel)
        rgbskel[rgbskel > 0] = 255 # makes lines appear thicker and easier to see.
        debug_ims.append(rgbskel)

        # add circle to show location of extracted region
        im_y = round(seed_centroid[0] * im.shape[0])
        im_x = round(seed_centroid[1] * im.shape[1])

        # inner_radius and outer_radius is specified relative to the segmentation.
        # We rescale the coordinates to the image, just in case the image is somehow different
        im_outer_radius = round(outer_radius * (im.shape[0] / skel.shape[0]))
        im_inner_radius = round(inner_radius * (im.shape[0] / skel.shape[0]))

        rr, cc  = circle_perimeter(im_y, im_x, im_inner_radius)
        rr = [r if r > im_y else im_y for r in rr] # semi circle will be used.
        # make sure they are inside the image to avoid an error.
        rr = [min(max(r, 0), im.shape[0]-1) for r in rr]
        cc = [min(max(c, 0), im.shape[1]-1) for c in cc]

        # create a red line image, so I can brighten it a bit by setting any pixel above 0 to max value.
        red_line_im = np.zeros(im.shape)

        red_line_im[rr, cc, 0] =  1.0
        
        rr, cc  = circle_perimeter(im_y, im_x, im_outer_radius)
        rr = [r if r > im_y else im_y for r in rr] # semi circle will be used.
        # make sure they are inside the image to avoid an error.
        rr = [min(max(r, 0), im.shape[0]-1) for r in rr]
        cc = [min(max(c, 0), im.shape[1]-1) for c in cc]

        red_line_im[rr, cc, 0] =  1.0

        red_im = fix_first_row_im(red_line_im)
        im = fix_first_row_im(im)
        im[red_im > 0] = 255
        debug_ims.append(im)

    # then take larger disk and set to 0 if outside
    rr, cc = disk((y, x), inner_radius)
    rr = [r if r > y else y for r in rr] # semi circle will be used.
    # make sure values are inside the image.
    rr = [min(max(r, 0), mask.shape[0]-1) for r in rr]
    cc = [min(max(c, 0), mask.shape[1]-1) for c in cc]
    mask[rr, cc] = 1

    rr, cc = disk((y, x), outer_radius)
    rr = [r if r > y else y for r in rr] # semi circle will be used.

    # make sure values are inside the image.
    rr = [min(max(r, 0), mask.shape[0]-1) for r in rr]
    cc = [min(max(c, 0), mask.shape[1]-1) for c in cc]

    mask[rr, cc] = 1
    
    skel[mask < 1] = 0

    y_start = max(0, y-(outer_radius+20))

    if save_debug_image:
        debug_ims.append(gray2rgb(skel[y_start:y+(outer_radius+20),
                                       x-(outer_radius+20):x+(outer_radius+20)]))

    # hide inner circle (less than inner radius)
    rr, cc = disk((y, x), inner_radius)
    rr = [r if r > y else y for r in rr] # semi circle will be used.
    # make sure values are inside the image.
    rr = [min(max(r, 0), mask.shape[0]-1) for r in rr]
    cc = [min(max(c, 0), mask.shape[1]-1) for c in cc]
    mask[rr, cc] = 0
    skel[mask < 1] = 0

    if save_debug_image:
        y_start = max(0, y-(outer_radius+20))
        debug_ims.append(gray2rgb(skel[y_start:y+(outer_radius+20),
                                       x-(outer_radius+20):x+(outer_radius+20)]))

    # take the regions left.
    # get the ones with the min and max x values.
    smallest_x_region = None
    largest_x_region = None
    label_img = label(skel)
    props = regionprops(label_img)

    if len(props) < 2:
        if save_debug_image:
            return None, get_merged_debug_im(debug_ims), 'could not find two roots in local region'
        return None, None, 'could not find two roots in local region'

    for region in props:
        if not smallest_x_region or (region.centroid[1] < smallest_x_region.centroid[1]):
            smallest_x_region = region
        if not largest_x_region or (region.centroid[1] > largest_x_region.centroid[1]):
            largest_x_region = region

    if save_debug_image:
        region_im = np.zeros(skel.shape)
        region_im[round(smallest_x_region.centroid[0]), round(smallest_x_region.centroid[1])] = 1
        region_im[round(largest_x_region.centroid[0]), round(largest_x_region.centroid[1])] = 1
        region_im[round(y), round(x)] = 1
        
        region_im = binary_dilation(region_im)
        region_im = binary_dilation(region_im)
        region_im = binary_dilation(region_im)
        region_im = binary_dilation(region_im)
        region_im = binary_dilation(region_im)
        y_start = max(0, y-(outer_radius+20))
        debug_ims.append(gray2rgb(region_im[y_start:y+(outer_radius+20),
                                            x-(outer_radius+20):x+(outer_radius+20)]))

    # get angle between the three points.
    a = np.array([smallest_x_region.centroid[1], smallest_x_region.centroid[0]])
    b = np.array([x, y])
    c = np.array([largest_x_region.centroid[1], largest_x_region.centroid[0]])
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)

    # https://manivannan-ai.medium.com/find-the-angle-between-three-points-from-2d-using-python-348c513e2cd
    angle_degrees = round(np.degrees(angle), 1)

    if save_debug_image:
        angle_im = add_text(skel, f'{angle_degrees}°', x=x, y=y-60)
        angle_im = gray2rgb(angle_im)
        # draw line to indicate detected position of primary roots.
        angle_im[:, :, 0] = draw_line(angle_im[:, :, 0], y1=y, x1=x, y2=a[1], x2=a[0])
        angle_im[:, :, 0] = draw_line(angle_im[:, :, 0], y1=y, x1=x, y2=c[1], x2=c[0])
        debug_ims.append(angle_im[y_start:y+(outer_radius+20),
                                  x-(outer_radius+20):x+(outer_radius+20)])

    if save_debug_image:
        merged = get_merged_debug_im(debug_ims)
    else:
        merged = None

    return angle_degrees, merged, None


def read_root_seg(im):
    """ convert segmentation {im} to skeleton
        and remove segments smaller than 30 pixels """
    skel = skeletonize(im)
    skel = remove_small_objects(skel, 30, connectivity=skel.ndim)
    return skel

def draw_line(img, y1, x1, y2, x2):
    """ draw a straight line from x1,y1 to x2,y2 on img """
    rr, cc, val = line_aa(round(y1), round(x1), round(y2), round(x2))
    img[rr, cc] = val * 255
    return img

def add_text(image, text, x, y):
    """
    Example usage.
    text_im = add_text(np.zeros((300, 300)),
                       f'{70 + i}°', x=50, y=50)
    """
    img = Image.new("1", (image.shape[1], image.shape[0]), (0))
    draw = ImageDraw.Draw(img)

    font = font_manager.FontProperties(family='sans-serif', weight='bold')
    fontfile = font_manager.findfont(font)
    # use a truetype font
    font = ImageFont.truetype(fontfile, 42)
    draw.text((x, y), text, (1), font=font)
    text_im = np.array(img)
    image[text_im > 0] = 1
    return image


def get_angles_from_image(seg_dataset_dir, im_dataset_dir, seed_seg_dir,
                          max_seed_points_per_im, inner_radius,
                          outer_radius, debug_image_dir, save_debug_image,
                          output_csv_path,
                          error_csv_path,
                          fname):


    """
    Extract angles from {fname} 
    and debug information to the debug_images folder.
    """
    im = None
    # we don't know what extension the original files have. Go through the common ones
    for ext in ['.JPG', '.JPEG', '.PNG', '.TIFF']:
        path = os.path.join(im_dataset_dir, os.path.splitext(fname)[0] + ext)
        if os.path.isfile(path):
            im = imread(path)
            break
        path = os.path.join(im_dataset_dir, os.path.splitext(fname)[0] + ext.lower())
        if os.path.isfile(path):
            im = imread(path)
            break
    if im is None:
        raise Exception(f'Cound not find photo for {fname} in {im_dataset_dir}')
    seg_im = imread(os.path.join(seg_dataset_dir, fname))[:, :, 3].astype(bool)

    seed_im = imread(os.path.join(seed_seg_dir, fname))[:, :, 3].astype(bool)

    ## change seed_im shape to be same size as seg_im. We assume its at the top of the image.

    # seed im could be smaller.
    # We assume the width of the seed im covers the full width of the image
    # i.e seed_im.shape[1] (width) is a scaled down version of seg_im.shape[1]
    scale_coef = seg_im.shape[1] / seed_im.shape[1]
    seed_im_new_height = round(seed_im.shape[0] * scale_coef)
    seed_im = resize(seed_im, (seed_im_new_height, seg_im.shape[1]))

    new_seed_im = np.zeros(seg_im.shape)
    # add seed im to the top of a blank image
    new_seed_im[:seed_im.shape[0], :seed_im.shape[1]] = seed_im.astype(int)
    seed_im = new_seed_im.astype(bool)
    skel = read_root_seg(seg_im)

    centroids, seed_masks, seed_pixels = load_seed_points(seed_im, max_seed_points_per_im)

    error_fnames = []
    errors = []
    for i, (c, seed_mask, seed_size) in enumerate(zip(centroids, seed_masks, seed_pixels)):

        angle_degrees, debug_image, error = get_primary_root_angle(c, inner_radius, outer_radius,
                                                                   im, seg_im, seed_mask,
                                                                   skel, save_debug_image)
        if angle_degrees:
            print(f"{fname},{angle_degrees},{i},{c[1]},{c[0]},{seed_size}",
                  file=open(output_csv_path, 'a'))
        if error:
            print(f"'error:{fname},{error},{i}")
            print(f"{fname},{error},{i},{c[1]},{c[0]},{seed_size}",
                  file=open(error_csv_path, 'a'))
            error_fnames.append(fname)
            errors.append(error)

        if debug_image is not None:
            # strange rounding/precision error left something slightly larger than 1
            # so we now restrict to max of 1.0
            imsave(os.path.join(debug_image_dir,
                                f"{fname.replace('.png', '')}_{i}.jpg"),
                                debug_image.astype(np.uint8), quality=95)
    return error_fnames, errors

def extract_all_angles(root_seg_dir, im_dataset_dir,
                       seed_seg_dir, max_seed_points_per_im,
                       debug_image_dir,
                       output_csv_path,
                       error_csv_path,
                       inner_radius=220,
                       outer_radius=300):
    """
    Go thorugh all images and extract all primary root angles (up to max 2 per image)
    """
    print('Extract all angles')
    assert outer_radius > inner_radius, 'outer radius must be bigger than inner radius'

    # if the debug folder doesn't already exist then it will be created.
    if not os.path.isdir(debug_image_dir):
        print(f'Creating {debug_image_dir}')
        os.makedirs(debug_image_dir)
    
    seg_fnames = os.listdir(seed_seg_dir)
    print('Seed segmentations', len(seg_fnames))
    seg_fnames = [s for s in seg_fnames if '.png' in s]

    print('Extract all angles from', len(seg_fnames), 'seeg segmentations')

    print("file_name,angle_degrees,seed_index,seed_x,seed_y,seed_pixels",
          file=open(output_csv_path, 'w+'))

    print("file_name,error_message,seed_index,seed_x,seed_y,seed_pixels",
          file=open(error_csv_path, 'w+'))
    start = time.time()
    for fname in seg_fnames:
        print(f"Extracting angles:{seg_fnames.index(fname) + 1}/{len(seg_fnames)}", fname)
        try:
            get_angles_from_image(root_seg_dir, im_dataset_dir,
                                  seed_seg_dir,
                                  max_seed_points_per_im,
                                  inner_radius,
                                  outer_radius,
                                  debug_image_dir,
                                  save_debug_image=True,
                                  output_csv_path=output_csv_path,
                                  error_csv_path=error_csv_path,
                                  fname=fname)

        # csv_file, error_file,
        except Exception as error:
            print(fname, error)
            print('file_name,{error},NA,NA,NA,NA', file=open(error_csv_path, 'a'))
            raise error

    time_str = humanize.naturaldelta(datetime.timedelta(seconds=time.time() - start))
    print('Extracting angles for', len(seg_fnames), 'images took', time_str)
