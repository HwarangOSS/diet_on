from PIL import Image

SRC = "diskcleaner/gui/assets/icon/icon.ico" 
OUT = "diskcleaner/gui/assets/icon/icon.ico"

img = Image.open(SRC).convert("RGBA")

size = max(img.width, img.height)
square = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 투명 배경
offset = ((size - img.width) // 2, (size - img.height) // 2)
square.paste(img, offset, img)

square.save(OUT, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

print("완료:", Image.open(OUT).size)