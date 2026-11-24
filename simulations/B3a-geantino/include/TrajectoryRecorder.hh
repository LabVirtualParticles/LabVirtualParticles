/// \file TrajectoryRecorder.hh
/// \brief Geantino Labs (IFPR) — mesmo formato de trajetorias.json do FolhaDeOuro
///
/// Registra as trajetorias (pontos por passo) de todas as particulas de
/// uma run e exporta em JSON no fim. Preenchido pelo SteppingAction,
/// escrito pelo RunAction. Diferencas para a versao do FolhaDeOuro:
///   - busca da trajetoria por mapa (o B3 gera muitas trajetorias por
///     evento; a busca linear deixava a run quadratica);
///   - limite de pontos, para o JSON nao ficar grande demais para o
///     navegador. Ao passar do limite, para de gravar e marca "truncated".

#ifndef GeantinoTrajectoryRecorder_h
#define GeantinoTrajectoryRecorder_h 1

#include <array>
#include <cstddef>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace Geantino
{

struct TrackRecord
{
    int event = 0;
    int track = 0;
    std::string particle;
    int charge = 0;
    std::vector<std::array<double, 3>> points;  // x,y,z em cm
};

class TrajectoryRecorder
{
  public:
    static TrajectoryRecorder* Instance();

    void AddPoint(int eventID, int trackID, const std::string& particleName, int charge,
                  double x_cm, double y_cm, double z_cm);
    void Clear();
    void WriteJSON(const std::string& filename) const;

    bool IsTruncated() const { return fTruncated; }
    std::size_t PointCount() const { return fPointCount; }

    // ~300 mil pontos ~ 10 MB de JSON: ainda leve para o navegador
    static constexpr std::size_t kMaxPoints = 300000;

  private:
    TrajectoryRecorder() = default;
    static TrajectoryRecorder* fInstance;

    std::vector<TrackRecord> fTracks;
    std::map<std::pair<int, int>, std::size_t> fIndex;  // (evento, track) -> posicao
    std::size_t fPointCount = 0;
    bool fTruncated = false;
};

}  // namespace Geantino

#endif
