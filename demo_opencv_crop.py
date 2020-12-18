import cv2

image = cv2.imread('/home/congdanh/Desktop/abc.jpg')

# (x,y,w,h) = cv2.selectROI(image)

x=0
y=0
h=1000
w=1000
# ROI = image[y:y+h, x:x+w]
#
# cv2.imshow("ROI", ROI)
# cv2.imwrite("ROI.png", ROI)
# cv2.waitKey(0)

crop_img = image[y:y+h, x:x+w]
cv2.imshow("cropped", crop_img)
# cv2.waitKey(0)
cv2.imwrite("crop.png", crop_img)