import math
import random
import sys
import time

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：敵SurfaceのRect
    引数2 dst：敵の標的になっているSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Hero(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)

    def get_direction(self) -> tuple[int, int]:
        return self.dire
    

class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    genemy = [(random.randint(0, WIDTH), 0), (random.randint(0, WIDTH), HEIGHT), (0, random.randint(0, HEIGHT)), (WIDTH, random.randint(0, HEIGHT))]
    
    def __init__(self, tower):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.choice(__class__.genemy)
        self.vx, self.vy = calc_orientation(self.rect, tower.rect)
        self.rect.centerx = self.rect.centerx
        self.rect.centery = self.rect.centery+self.rect.height/2
        self.speed = 6

    def update(self, tower, hero: Hero, hate):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数1 screen：画面Surface
        引数2 towerオブジェクト
        引数3 heroオブジェクト
        引数4 enenmyの攻撃対象を決める変数(tower or hero)
        """
        if hate == "tower":
            self.vx, self.vy = calc_orientation(self.rect, tower.rect)
        elif hate == "hero":
            self.vx, self.vy = calc_orientation(self.rect, hero.rect)
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)


class Tower(pg.sprite.Sprite):
    """
    タワーに関するクラス
    """
    def __init__(self):
        super().__init__()
        self.life = 3
        color = (0, 0, 0)
        self.image = pg.Surface((50, 50))
        pg.draw.rect(self.image, color, pg.Rect(0, 0, 20, 20))
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH/2
        self.rect.centery = HEIGHT/2
    def update(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    敵機：1点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)
    

def main():
    pg.display.set_caption("守れ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    score = Score()
    hate = "tower"  # 敵機の攻撃対象をtowerに設定

    hero = Hero(3, (900, 400))
    tower = Tower()
    emys = pg.sprite.Group()
    emys = pg.sprite.Group()


    tmr = 0
    trans_hate_tm = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and score.score >= 10:
                hate = "hero"  # 敵機の攻撃対象をheroに設定
                trans_hate_tm = 0
                score.score_up(-10)
        screen.blit(bg_img, [0, 0])
         
        if trans_hate_tm > 100:  # 100フレーム経過後
            hate = "tower"  # 敵機の攻撃対象をtowerにリセット

        if tmr%40 == 0:  # 40フレームに1回，敵機を出現させる
            emys.add(Enemy(hero))

        for i in pg.sprite.spritecollide(hero, emys, True):
            score.score_up(1)

        for i in pg.sprite.spritecollide(tower, emys, True):
            tower.life -= 1
            if tower.life <= 0:
                hero.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        hero.update(key_lst, screen)
        emys.update(tower, hero, hate)
        emys.draw(screen)
        tower.update(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        trans_hate_tm += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
