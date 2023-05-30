import math
import random
import sys
import time
import os

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ

def load_sound(file):
    """指定した名称のファイルをfigフォルダから出して
    音を出力する準備をする
    """

    file = os.path.join( "fig", file)
    sound = pg.mixer.Sound(file)
    return sound

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
    主人公）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self,  xy: tuple[int, int]):
        """
        主人公画像Surfaceを生成する
        引数2 xy：主人公画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/hero.png"), 0, 0.1)
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
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.1)
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
    imgs = [pg.transform.rotozoom(pg.image.load(f"fig/ene{i}.png"),0,0.15) for i in range(1, 4)]
    genemy = [(random.randint(0, WIDTH), 0), (random.randint(0, WIDTH), HEIGHT), (0, random.randint(0, HEIGHT)), (WIDTH, random.randint(0, HEIGHT))]
    
    def __init__(self, tower):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.choice(__class__.genemy)
        self.vx, self.vy = calc_orientation(self.rect, tower.rect)
        self.rect.centerx = self.rect.centerx
        self.rect.centery = self.rect.centery+self.rect.height/2
        self.speed = 5

    def update(self, tower, hero: Hero, hate):
        """
        敵を速度ベクトルself.vx, self.vyに基づき移動させる
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
    def __init__(self) :
        super().__init__()
        self.image=pg.transform.rotozoom(pg.image.load(f"fig/tower.png"), 0, 0.8)
        self.life = 3
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2,HEIGHT/2
        self.super = 0
        self.font = pg.font.Font(None, 50)  #life表示のための用意
        self.color = (255, 0 , 0)
        self.displife = self.font.render(f"Life: {self.life}", 0, self.color)

    def update(self, screen: pg.Surface):
        """
        現在のlifeやタワーを表示する
        """
        screen.blit(self.image,self.rect)
        self.displife = self.font.render(f"Life: {self.life}", 0, self.color)
        screen.blit(self.displife,(30,HEIGHT-125))    
        self.rect.centerx = WIDTH/2
        self.rect.centery = HEIGHT/2
        self.super -= 1

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


class Boss(pg.sprite.Sprite):
    """
    ボスに関するクラス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/alien1.png"), 0, 3.0)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, -3000
        self.bound = 100  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.skill_wait = 100
        self.vy = 6
        self.vx = 0
        self.count_charge = 0

    def update(self, screen):
        """
        ボスを速度ベクトルself.vyに基づき移動（降下）させる
        停止位置_boundまで降下したら，_stateを停止状態に変更する
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
    
        if self.rect.centerx <= 0:
            self.skill_wait = random.randint(50, 300)
            self.count_charge += 1
            if self.count_charge > 5:
                self.state = "down"
                self.rect.center = WIDTH/2, 200
                self.vx = 0
                self.vy = -10
        if self.rect.centery <= -5000:
            self.vy = 6
            self.count_charge = 0

        self.rect.centery += self.vy
        self.rect.centerx += self.vx
        screen.blit(self.image, self.rect)

    def charge(self, hero: Hero):
        """
        ボスがhero.rectから主人公のy座標を薙ぎ払うように突進する
        """
        if self.skill_wait > 0:
            self.vx, self.vy = 0, 0
            self.rect.center = WIDTH, hero.rect.centery
            self.skill_wait -= 1
        else:
            self.vx = -25


def main():
    pg.display.set_caption("守れ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/bg_natural_mori.jpg")
    atk_sound = load_sound("紙を破く1.mp3")
    end_sound = load_sound("チーン1.mp3")
    score = Score()
    fonto  = pg.font.Font(None, 50)

    hero = Hero( (900, 400))
    tower = Tower()
    emys = pg.sprite.Group()
    emys = pg.sprite.Group()
    hate = "tower"  # 敵機の攻撃対象をtowerに設定
    boss = Boss()
    mode = False

    tmr = 0
    trans_hate_tm = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and score.score >= 5:
                hate = "hero"  # 敵機の攻撃対象をheroに設定
                trans_hate_tm = 0
                score.score_up(-5)
            if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                mode = True

        screen.blit(bg_img, [0, 0])
         
        if trans_hate_tm > 100:  # 100フレーム経過後
            hate = "tower"  # 敵機の攻撃対象をtowerにリセット

        if tmr%80 == 0:  # 40フレームに1回，敵機を出現させる
            emys.add(Enemy(hero))

        if mode == True and tmr%200 == 0:
            emys.add(Enemy(hero))
            Enemy.speed = 8

        for emy in pg.sprite.spritecollide(hero, emys, True):
                emy.kill()
                if pg.mixer:
                    atk_sound.play()
                score.score_up(1)

        for emy in pg.sprite.spritecollide(tower, emys, True):
            if tower.life >= 2:
                tower.life -=1  #lifeを減らす
                emy.kill()  
            else:
                screen.blit(pg.transform.rotozoom(pg.image.load("fig/text_gameover.png"),0,0.4),[600,250])
                hero.change_img("lose", screen) # 悲しみエフェクト
                end_sound.play()
                tower.life -=1
                score.update(screen)
                tower.update(screen)
                screen.blit(txt_time, [WIDTH/2, 50])
                pg.display.update()
                time.sleep(2)
                return
            
        if boss.state == "stop":
            boss.charge(hero)



        if pg.sprite.collide_rect(boss, tower):
            if tower.super <= 0:
                tower.life -= 1
                tower.super = 100
                if tower.life <= 0:
                    screen.blit(pg.transform.rotozoom(pg.image.load("fig/text_gameover.png"),0,0.4),[600,250])
                    hero.change_img("lose", screen) # 悲しみエフェクト
                    tower.life -=1
                    score.update(screen)
                    tower.update(screen)
                    screen.blit(txt_time, [WIDTH/2, 50])
                    pg.display.update()
                    time.sleep(2)
                    return
          
        txt_time = fonto.render(str(tmr/50), True, (0, 0 ,0 ))
        screen.blit(txt_time, [WIDTH/2, 50])
        hero.update(key_lst, screen)
        emys.update(tower, hero, hate)
        emys.draw(screen)
        boss.update(screen)
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
