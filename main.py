# --- インポート ---
import pygame
import random as r
import numpy as np
import math
import asyncio

# --- 設定 ---
WIDTH, HEIGHT = 1000, 400
FPS = 60
POP_SIZE = 25       # 個体数
GENE_LENGTH = 100    # 動作ステップ数：関節の角度指定
LIFESPAN = 300       # 1世代の寿命：フレーム数
MUTATION_RATE = 0.05  # 突然変異率

WHITE = (255, 255, 255)
BLACK = (30, 30, 30)

# --- クラス定義 ---
class Creature:
  # 個体
  def __init__(self, genes=None, color=None):
    self.start_x = 100
    self.x = self.start_x
    self.y = HEIGHT - 50

    if color is None:
      self.color = (r.randint(50, 255),
                    r.randint(50, 255),
                    r.randint(50, 255))
    else:
      self.color = color

    if genes is None:
      self.genes = np.random.uniform(-45, 45, (GENE_LENGTH, 2))
    else:
      self.genes = genes

    self.fitness = 0
    self.thigh_angle = 0  # 太ももの角度
    self.knee_angle = 0   # ひざの角度
    self.timer = 0

# 更新
  def update(self):
    gene_idx = (self.timer // 5) % GENE_LENGTH
    # 遺伝子から目標角度を取得
    target_thigh = self.genes[gene_idx, 0]
    target_knee = self.genes[gene_idx, 1]

    knee_y = self.y + 30 * math.cos(math.radians(target_thigh))
    foot_y = knee_y + 30 * \
        math.cos(math.radians(target_thigh + target_knee))

    ground_y = HEIGHT - 50
    if foot_y >= ground_y:
      diff = (target_knee - self.knee_angle) + (target_thigh - self.thigh_angle)
      if diff > 0:
        self.x += diff * 0.4
      self.y = ground_y - (foot_y - self.y)
    else:
      if self.y < ground_y - 10:
        self.y += 1.0

    self.thigh_angle = target_thigh
    self.knee_angle = target_knee
    self.timer += 1

  # 描画
  def draw(self, screen, camera_x):
    draw_x = self.x - camera_x
    draw_y = self.y

    if draw_x < -100 or draw_x > WIDTH + 100:
      return

    color = self.color

    knee_x = self.x + 30 * math.sin(math.radians(self.thigh_angle))
    knee_y = self.y + 30 * math.cos(math.radians(self.thigh_angle))
    foot_x = knee_x + 30 * \
        math.sin(math.radians(self.thigh_angle + self.knee_angle))
    foot_y = knee_y + 30 * \
        math.cos(math.radians(self.thigh_angle + self.knee_angle))

    # 描画：体 -> ひざ -> 足先
    pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 10)  # 付け根
    pygame.draw.line(screen, color, (self.x, self.y),
                     (knee_x, knee_y), 4)  # 太もも
    pygame.draw.line(screen, color, (knee_x, knee_y),
                     (foot_x, foot_y), 2)  # すね

    face_center_x = draw_x
    face_center_y = draw_y - 5  # 体の中心より少し上に頭があるようないめーじ

    pygame.draw.circle(
        screen, BLACK, (int(face_center_x - 4), int(face_center_y - 3)), 1)
    pygame.draw.circle(
        screen, BLACK, (int(face_center_x + 4), int(face_center_y - 3)), 1)
    pygame.draw.line(screen, BLACK, (int(face_center_x - 5), int(face_center_y + 5)),
                     (int(face_center_x + 5), int(face_center_y + 5)), 1)

# --- メインループ ---
async def main():
  pygame.init()
  screen = pygame.display.set_mode((WIDTH, HEIGHT))
  clock = pygame.time.Clock()
  font = pygame.font.SysFont("arial", 24)
  result_font = pygame.font.SysFont("arial", 60)  

  population = [Creature() for _ in range(POP_SIZE)]
  generation = 1
  frame_count = 0
  best_distance_all_time = 0.0
  camera_x = 0

  state = "PLAY"
  running = True

  while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False

      # --- リスタートボタンのクリック判定 ---
      if event.type == pygame.MOUSEBUTTONDOWN and state == "RESULT":
        mx, my = event.pos
        # 画面中央のボタン範囲内ならリセット
        if WIDTH // 2 - 100 < mx < WIDTH // 2 + 100 and HEIGHT // 2 + 50 < my < HEIGHT // 2 + 100:
          generation = 1
          best_distance_all_time = 0.0
          camera_x = 0
          population = [Creature() for _ in range(POP_SIZE)]
          frame_count = 0
          state = "PLAY"

    if state == "PLAY":
      furthest_x = max([c.x for c in population])
      current_dist = furthest_x - 100
      if current_dist > best_distance_all_time:
        best_distance_all_time = current_dist

      target_camera_x = furthest_x - 500
      if target_camera_x > camera_x:
        camera_x += (target_camera_x - camera_x) * 0.1

      # グリッド・地面・最高ラインの描画
      for i in range(int(camera_x // 100), int((camera_x + WIDTH) // 100) + 1):
        line_x = i * 100 - camera_x
        pygame.draw.line(screen, (50, 50, 50), (line_x,
                         HEIGHT - 50), (line_x, HEIGHT - 40), 1)
      pygame.draw.line(screen, WHITE, (0, HEIGHT - 50),
                       (WIDTH, HEIGHT - 50), 2)
      goal_x = 100 + best_distance_all_time - camera_x
      if -10 < goal_x < WIDTH + 10:
        pygame.draw.line(screen, (255, 255, 0),
                         (goal_x, 0), (goal_x, HEIGHT - 50), 3)

      # 更新と描画
      for c in population:
        c.update()
        c.draw(screen, camera_x)

      # UI表示
      dist_m = best_distance_all_time / 100.0
      dist_text = font.render(
          f"All-time Best: {dist_m:.2f} m", True, (255, 255, 0))
      info = font.render(
          f"Gen: {generation}  Time: {frame_count}/{LIFESPAN}", True, WHITE)
      screen.blit(info, (10, 10))
      screen.blit(dist_text, (10, 40))

      # --- 世代交代のチェック ---
      frame_count += 1
      if frame_count > LIFESPAN:
        # 世代判定
        if generation >= 20: # ここの値を変えると世代数の上限を変更可能
          state = "RESULT"
        else:
          for c in population:
            c.fitness = max(0.1, c.x - c.start_x)
          population.sort(key=lambda x: x.fitness, reverse=True)
          best_creature = population[0]
          new_pop = [Creature(best_creature.genes,
                              color=best_creature.color)]
          while len(new_pop) < POP_SIZE:
            parent = best_creature
            child_genes = parent.genes.copy()
            if r.random() < 0.5:
              row = r.randint(0, GENE_LENGTH - 1)
              col = r.randint(0, 1)
              child_genes[row, col] += r.uniform(-20, 20)
            new_pop.append(
                Creature(child_genes, color=parent.color))
          population = new_pop
          generation += 1
          frame_count = 0

    elif state == "RESULT":
      # --- リザルト画面の描画 ---
      res_text = result_font.render("FINAL RESULT", True, WHITE)
      score_text = font.render(
          f"Top Record: {best_distance_all_time/100.0:.2f} m", True, (255, 255, 0))

      screen.blit(
          res_text, (WIDTH // 2 - res_text.get_width() // 2, HEIGHT // 2 - 80))
      screen.blit(score_text, (WIDTH // 2 -
                  score_text.get_width() // 2, HEIGHT // 2))

      # ボタン描画
      pygame.draw.rect(screen, (80, 80, 80),
                       (WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50))
      btn_text = font.render("RESTART", True, WHITE)
      screen.blit(
          btn_text, (WIDTH // 2 - btn_text.get_width() // 2, HEIGHT // 2 + 60))

    pygame.display.flip()
    clock.tick(FPS)
    await asyncio.sleep(0)

  pygame.quit()
if __name__ == "__main__":
  asyncio.run(main())
