import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import numbers
import random
import time

from skimage.util.shape import view_as_windows
from skimage.transform import resize
from skimage.transform import rescale

class RandGray(object):
    def __init__(self,  
                 batch_size, 
                 p_rand=0.5,
                 *_args, 
                 **_kwargs):
        
        self.p_gray = p_rand
        self.batch_size = batch_size
        self.random_inds = np.random.choice([True, False], 
                                            batch_size, 
                                            p=[self.p_gray, 1 - self.p_gray])
        
    def grayscale(self, imgs):
        # imgs: b x h x w x c
        b, h, w, c = imgs.shape
        imgs = imgs[:, :, :, 0] * 0.2989 + imgs[:, :, :, 1] * 0.587 + imgs[:, :, :, 2] * 0.114 
        imgs = np.tile(imgs.reshape(b,h,w,-1), (1, 1, 1, 3)).astype(np.uint8)
        return imgs

    def do_augmentation(self, images):
        # images: [B, C, H, W]
        bs, channels, h, w = images.shape    
        if self.random_inds.sum() > 0:
            images[self.random_inds] =  self.grayscale(images[self.random_inds])

        return images
    
    def change_randomization_params(self, index_):
        self.random_inds[index_] = np.random.choice([True, False], 1, 
                                                    p=[self.p_gray, 1 - self.p_gray])
        
    def change_randomization_params_all(self):
        self.random_inds = np.random.choice([True, False], 
                                            self.batch_size, 
                                            p=[self.p_gray, 1 - self.p_gray])
        
    def print_parms(self):
        print(self.random_inds)
        
        
class Cutout(object):
    def __init__(self, 
                 batch_size, 
                 box_min=7, 
                 box_max=22, 
                 pivot_h=12, 
                 pivot_w=24,
                 *_args, 
                 **_kwargs):
        
        self.box_min = box_min
        self.box_max = box_max
        self.pivot_h = pivot_h
        self.pivot_w = pivot_w
        self.batch_size = batch_size
        self.w1 = np.random.randint(self.box_min, self.box_max, batch_size)
        self.h1 = np.random.randint(self.box_min, self.box_max, batch_size)
        
    def do_augmentation(self, imgs):
        n, h, w, c = imgs.shape
        cutouts = np.empty((n, h, w, c), dtype=imgs.dtype)
        for i, (img, w11, h11) in enumerate(zip(imgs, self.w1, self.h1)):
            cut_img = img.copy()
            cut_img[self.pivot_h+h11:self.pivot_h+h11+h11, 
                    self.pivot_w+w11:self.pivot_w+w11+w11, :] = 0
            cutouts[i] = cut_img
        return cutouts
    
    def change_randomization_params(self, index_):
        self.w1[index_] = np.random.randint(self.box_min, self.box_max)
        self.h1[index_] = np.random.randint(self.box_min, self.box_max)

    def change_randomization_params_all(self):
        self.w1 = np.random.randint(self.box_min, self.box_max, self.batch_size)
        self.h1 = np.random.randint(self.box_min, self.box_max, self.batch_size)
        
    def print_parms(self):
        print(self.w1)
        print(self.h1)
        
        
class Cutout_Color(object):
    def __init__(self, 
                 batch_size, 
                 box_min=7, 
                 box_max=22, 
                 pivot_h=12, 
                 pivot_w=24, 
                 obs_dtype='uint8', 
                 *_args, 
                 **_kwargs):
        
        self.box_min = box_min
        self.box_max = box_max
        self.pivot_h = pivot_h
        self.pivot_w = pivot_w
        self.batch_size = batch_size
        self.w1 = np.random.randint(self.box_min, self.box_max, batch_size)
        self.h1 = np.random.randint(self.box_min, self.box_max, batch_size)
        self.rand_box = np.random.randint(0, 255, size=(batch_size, 1, 1, 3), dtype=obs_dtype)
        self.obs_dtype = obs_dtype
        
    def do_augmentation(self, imgs):
        n, h, w, c = imgs.shape
        pivot_h = 12
        pivot_w = 24

        cutouts = np.empty((n, h, w, c), dtype=imgs.dtype)
        for i, (img, w11, h11) in enumerate(zip(imgs, self.w1, self.h1)):
            cut_img = img.copy()
            cut_img[self.pivot_h+h11:self.pivot_h+h11+h11, self.pivot_w+w11:self.pivot_w+w11+w11, :] \
            = np.tile(self.rand_box[i], cut_img[self.pivot_h+h11:self.pivot_h+h11+h11, 
                                                self.pivot_w+w11:self.pivot_w+w11+w11, :].shape[:-1] +(1,))
            cutouts[i] = cut_img
        return cutouts
        
    def change_randomization_params(self, index_):
        self.w1[index_] = np.random.randint(self.box_min, self.box_max)
        self.h1[index_] = np.random.randint(self.box_min, self.box_max)
        self.rand_box[index_] = np.random.randint(0, 255, size=(1, 1, 1, 3), dtype=self.obs_dtype)

    def change_randomization_params_all(self):
        self.w1 = np.random.randint(self.box_min, self.box_max, self.batch_size)
        self.h1 = np.random.randint(self.box_min, self.box_max, self.batch_size)
        self.rand_box = np.random.randint(0, 255, size=(self.batch_size, 1, 1, 3), dtype=self.obs_dtype)
        
    def print_parms(self):
        print(self.w1)
        print(self.h1)
        
class Rand_Flip(object):
    def __init__(self,  
                 batch_size, 
                 p_rand=0.5,
                 *_args, 
                 **_kwargs):
        
        self.p_flip = p_rand
        self.batch_size = batch_size
        self.random_inds = np.random.choice([True, False], 
                                            batch_size, 
                                            p=[self.p_flip, 1 - self.p_flip])
        
    def do_augmentation(self, images):
        if self.random_inds.sum() > 0:
            images[self.random_inds] = np.flip(images[self.random_inds], 2)
        return images
    
    def change_randomization_params(self, index_):
        self.random_inds[index_] = np.random.choice([True, False], 1, 
                                                    p=[self.p_flip, 1 - self.p_flip])

    def change_randomization_params_all(self):
        self.random_inds = np.random.choice([True, False], 
                                            self.batch_size, 
                                            p=[self.p_flip, 1 - self.p_flip])
        
    def print_parms(self):
        print(self.random_inds)
        
class Rand_Rotate(object):
    def __init__(self,  
                 batch_size, 
                 *_args, 
                 **_kwargs):
        
        self.batch_size = batch_size
        self.random_inds = np.random.randint(4, size=batch_size) * batch_size + np.arange(batch_size)
        
    def do_augmentation(self, imgs):
        tot_imgs = imgs
        for k in range(3):
            rot_imgs = np.ascontiguousarray(np.rot90(imgs,k=(k+1),axes=(1,2)))
            tot_imgs = np.concatenate((tot_imgs, rot_imgs), 0)
        return tot_imgs[self.random_inds]
    
    def change_randomization_params(self, index_):
        temp = np.random.randint(4)            
        self.random_inds[index_] = index_ + temp * self.batch_size
        
    def change_randomization_params_all(self):
        self.random_inds = np.random.randint(4, size=self.batch_size) * self.batch_size + np.arange(self.batch_size)
        
    def print_parms(self):
        print(self.random_inds)
        
class Rand_Crop(object):
    def __init__(self,  
                 batch_size, 
                 *_args, 
                 **_kwargs):
        
        self.batch_size = batch_size
        self.crop_size = 64
        self.crop_max = 75 - self.crop_size
        self.w1 = np.random.randint(0, self.crop_max, self.batch_size)
        self.h1 = np.random.randint(0, self.crop_max, self.batch_size)
                
    def do_augmentation(self, imgs):
        # procgen give 64x64, thus first scale-up to 84, then crop back to 64
        # print('imgs before transpose', imgs.shape)
        n = imgs.shape[0]
        imgs_in = imgs
        imgs_out = np.zeros((n, 84, 84, 3))

        for m,i in enumerate(imgs_in):
            imgs_out[m,:,:,:] = resize(imgs_in[m,:,:,:], imgs_out.shape[1:], anti_aliasing=True)
        imgs = imgs_out


        # imgs = rescale(imgs, 1.32)
        # print('imgs after resize', imgs.shape)

        # batch size
       

        img_size = imgs.shape[1]
        imgs = np.transpose(imgs, (0, 2, 1, 3))
        # print('imgs.shape after transpose', imgs.shape)
        # creates all sliding windows combinations of size (output_size)
        # windows = view_as_windows(
        #     imgs, (1, self.crop_size, self.crop_size, 1))[..., 0,:,:, 0]
        windows = view_as_windows(imgs, (1, self.crop_size, self.crop_size, 1))
        # print('windows type', type(windows))
        # print('windows shape', windows.shape)
        windows = windows[..., 0,:,:, 0]
        # print('after index windows type', type(windows))
        # print('after index windows shape', windows.shape)
        
        # selects a random window for each batch element
        cropped_imgs = windows[np.arange(n), self.w1, self.h1]
        cropped_imgs = np.swapaxes(cropped_imgs,1,3)
        return cropped_imgs
    
    def change_randomization_params(self, index_):
        self.w1[index_] = np.random.randint(0, self.crop_max)
        self.h1[index_] = np.random.randint(0, self.crop_max)

    def change_randomization_params_all(self):
        self.w1 = np.random.randint(0, self.crop_max, self.batch_size)
        self.h1 = np.random.randint(0, self.crop_max, self.batch_size)
    
    def print_parms(self):
        print(self.w1)
        print(self.h1)
        
class Center_Crop(object):
    def __init__(self, 
                 *_args, 
                 **_kwargs):
        self.crop_size = 64
    
    def do_augmentation(self, image):
        h, w = image.shape[1], image.shape[2]
        new_h, new_w = self.crop_size, self.crop_size

        top = (h - new_h)//2
        left = (w - new_w)//2
        image = image[:, top:top + new_h, left:left + new_w, :]
        return image.copy()
    
    def change_randomization_params(self, index_):
        index_ = index_
        
    def change_randomization_params_all(self):
        index_ = 0
    
    def print_parms(self):
        print('nothing')
        
class ColorJitterLayer(nn.Module):
    def __init__(self, 
                 batch_size,
                 brightness=0.4,                              
                 contrast=0.4,
                 saturation=0.4, 
                 hue=0.5,
                 p_rand=1.0,
                 stack_size=1, 
                 *_args,
                 **_kwargs):
        super(ColorJitterLayer, self).__init__()
        self.brightness = self._check_input(brightness, 'brightness')
        self.contrast = self._check_input(contrast, 'contrast')
        self.saturation = self._check_input(saturation, 'saturation')
        self.hue = self._check_input(hue, 'hue', center=0, bound=(-0.5, 0.5),
                                     clip_first_on_zero=False)
        
        self.prob = p_rand
        self.batch_size = batch_size
        self.stack_size = stack_size
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#         self._device = torch.device('cpu')
    
        # random paramters
        factor_contrast = torch.empty(self.batch_size, device=self._device).uniform_(*self.contrast)
        self.factor_contrast = factor_contrast.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_hue = torch.empty(self.batch_size, device=self._device).uniform_(*self.hue)
        self.factor_hue = factor_hue.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_brightness = torch.empty(self.batch_size, device=self._device).uniform_(*self.brightness)
        self.factor_brightness = factor_brightness.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_saturate = torch.empty(self.batch_size, device=self._device).uniform_(*self.saturation)
        self.factor_saturate = factor_saturate.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        

        
    def _check_input(self, value, name, center=1, bound=(0, float('inf')), clip_first_on_zero=True):
        if isinstance(value, numbers.Number):
            if value < 0:
                raise ValueError("If {} is a single number, it must be non negative.".format(name))
            value = [center - value, center + value]
            if clip_first_on_zero:
                value[0] = max(value[0], 0)
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            if not bound[0] <= value[0] <= value[1] <= bound[1]:
                raise ValueError("{} values should be between {}".format(name, bound))
        else:
            raise TypeError("{} should be a single number or a list/tuple with lenght 2.".format(name))
        # if value is 0 or (1., 1.) for brightness/contrast/saturation
        # or (0., 0.) for hue, do nothing
        if value[0] == value[1] == center:
            value = None
        return value
    
    def adjust_contrast(self, x):
        """
            Args:
                x: torch tensor img (rgb type)
            Factor: torch tensor with same length as x
                    0 gives gray solid image, 1 gives original image,
            Returns:
                torch tensor image: Brightness adjusted
        """
        means = torch.mean(x, dim=(2, 3), keepdim=True)
        return torch.clamp((x - means)
                           * self.factor_contrast.view(len(x), 1, 1, 1) + means, 0, 1)
    
    def adjust_hue(self, x):
        h = x[:, 0, :, :]
        h += (self.factor_hue.view(len(x), 1, 1) * 255. / 360.)
        h = (h % 1)
        x[:, 0, :, :] = h
        return x
    
    def adjust_brightness(self, x):
        """
            Args:
                x: torch tensor img (hsv type)
            Factor:
                torch tensor with same length as x
                0 gives black image, 1 gives original image,
                2 gives the brightness factor of 2.
            Returns:
                torch tensor image: Brightness adjusted
        """
        x[:, 2, :, :] = torch.clamp(x[:, 2, :, :]
                                     * self.factor_brightness.view(len(x), 1, 1), 0, 1)
        return torch.clamp(x, 0, 1)
    
    def adjust_saturate(self, x):
        """
            Args:
                x: torch tensor img (hsv type)
            Factor:
                torch tensor with same length as x
                0 gives black image and white, 1 gives original image,
                2 gives the brightness factor of 2.
            Returns:
                torch tensor image: Brightness adjusted
        """
        x[:, 1, :, :] = torch.clamp(x[:, 1, :, :]
                                    * self.factor_saturate.view(len(x), 1, 1), 0, 1)
        return torch.clamp(x, 0, 1)
    
    def transform(self, inputs):
        hsv_transform_list = [rgb2hsv, self.adjust_brightness,
                              self.adjust_hue, self.adjust_saturate,
                              hsv2rgb]
        rgb_transform_list = [self.adjust_contrast]
        
        # Shuffle transform
        if random.uniform(0,1) >= 0.5:
            transform_list = rgb_transform_list + hsv_transform_list
        else:
            transform_list = hsv_transform_list + rgb_transform_list
        for t in transform_list:
            inputs = t(inputs)
        return inputs
    
    def do_augmentation(self, imgs):
        # batch size
        imgs = np.transpose(imgs, (0, 3, 2, 1))
        inputs = torch.from_numpy(imgs).to(self._device).float()
        inputs = inputs / 255.0
        
        outputs = self.forward(inputs)
        outputs = outputs.data.cpu().numpy() * 255.0
        outputs = np.transpose(outputs, (0, 3, 2, 1))
        return outputs
    
    def change_randomization_params(self, index_):
        self.factor_contrast[index_] = torch.empty(1, device=self._device).uniform_(*self.contrast)
        self.factor_hue[index_] = torch.empty(1, device=self._device).uniform_(*self.hue)
        self.factor_brightness[index_] = torch.empty(1, device=self._device).uniform_(*self.brightness)
        self.factor_saturate[index_] = torch.empty(1, device=self._device).uniform_(*self.saturation)

    def change_randomization_params_all(self):
        factor_contrast = torch.empty(self.batch_size, device=self._device).uniform_(*self.contrast)
        self.factor_contrast = factor_contrast.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_hue = torch.empty(self.batch_size, device=self._device).uniform_(*self.hue)
        self.factor_hue = factor_hue.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_brightness = torch.empty(self.batch_size, device=self._device).uniform_(*self.brightness)
        self.factor_brightness = factor_brightness.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
        factor_saturate = torch.empty(self.batch_size, device=self._device).uniform_(*self.saturation)
        self.factor_saturate = factor_saturate.reshape(-1,1).repeat(1, self.stack_size).reshape(-1)
        
    def print_parms(self):
        print(self.factor_hue)
        
    def forward(self, inputs):
        # batch size
        random_inds = np.random.choice(
            [True, False], len(inputs), p=[self.prob, 1 - self.prob])
        inds = torch.tensor(random_inds).to(self._device)
        if random_inds.sum() > 0:
            inputs[inds] = self.transform(inputs[inds])
        return inputs

def rgb2hsv(rgb, eps=1e-8):
    # Reference: https://www.rapidtables.com/convert/color/rgb-to-hsv.html
    # Reference: https://github.com/scikit-image/scikit-image/blob/master/skimage/color/colorconv.py#L287

    _device = rgb.device
    r, g, b = rgb[:, 0, :, :], rgb[:, 1, :, :], rgb[:, 2, :, :]

    Cmax = rgb.max(1)[0]
    Cmin = rgb.min(1)[0]
    delta = Cmax - Cmin

    hue = torch.zeros((rgb.shape[0], rgb.shape[2], rgb.shape[3])).to(_device)
    hue[Cmax== r] = (((g - b)/(delta + eps)) % 6)[Cmax == r]
    hue[Cmax == g] = ((b - r)/(delta + eps) + 2)[Cmax == g]
    hue[Cmax == b] = ((r - g)/(delta + eps) + 4)[Cmax == b]
    hue[Cmax == 0] = 0.0
    hue = hue / 6. # making hue range as [0, 1.0)
    hue = hue.unsqueeze(dim=1)

    saturation = (delta) / (Cmax + eps)
    saturation[Cmax == 0.] = 0.
    saturation = saturation.to(_device)
    saturation = saturation.unsqueeze(dim=1)

    value = Cmax
    value = value.to(_device)
    value = value.unsqueeze(dim=1)

    return torch.cat((hue, saturation, value), dim=1)#.type(torch.FloatTensor).to(_device)
    # return hue, saturation, value

def hsv2rgb(hsv):
    # Reference: https://www.rapidtables.com/convert/color/hsv-to-rgb.html
    # Reference: https://github.com/scikit-image/scikit-image/blob/master/skimage/color/colorconv.py#L287

    _device = hsv.device

    hsv = torch.clamp(hsv, 0, 1)
    hue = hsv[:, 0, :, :] * 360.
    saturation = hsv[:, 1, :, :]
    value = hsv[:, 2, :, :]

    c = value * saturation
    x = - c * (torch.abs((hue / 60.) % 2 - 1) - 1)
    m = (value - c).unsqueeze(dim=1)

    rgb_prime = torch.zeros_like(hsv).to(_device)

    inds = (hue < 60) * (hue >= 0)
    rgb_prime[:, 0, :, :][inds] = c[inds]
    rgb_prime[:, 1, :, :][inds] = x[inds]

    inds = (hue < 120) * (hue >= 60)
    rgb_prime[:, 0, :, :][inds] = x[inds]
    rgb_prime[:, 1, :, :][inds] = c[inds]

    inds = (hue < 180) * (hue >= 120)
    rgb_prime[:, 1, :, :][inds] = c[inds]
    rgb_prime[:, 2, :, :][inds] = x[inds]

    inds = (hue < 240) * (hue >= 180)
    rgb_prime[:, 1, :, :][inds] = x[inds]
    rgb_prime[:, 2, :, :][inds] = c[inds]

    inds = (hue < 300) * (hue >= 240)
    rgb_prime[:, 2, :, :][inds] = c[inds]
    rgb_prime[:, 0, :, :][inds] = x[inds]

    inds = (hue < 360) * (hue >= 300)
    rgb_prime[:, 2, :, :][inds] = x[inds]
    rgb_prime[:, 0, :, :][inds] = c[inds]

    rgb = rgb_prime + torch.cat((m, m, m), dim=1)
    rgb = rgb.to(_device)

    return torch.clamp(rgb, 0, 1)