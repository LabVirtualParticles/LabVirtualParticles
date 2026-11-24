#----------------------------------------------------------------------------
# B5 adaptado para o Geantino Labs (modo batch, sem parte grafica).
# Baseado no CMakeLists.txt do examples/basic/B5 da Colaboracao Geant4.
#
cmake_minimum_required(VERSION 3.16...3.27)
project(GeantinoB5)

# Sem ui_all/vis_all: este programa nao abre interface nem visualizacao.
# Precisa do Geant4 compilado com GDML (GEANT4_USE_GDML=ON).
find_package(Geant4 REQUIRED)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(geantinoB5 geantinoB5.cc ${sources} ${headers})
target_include_directories(geantinoB5 PRIVATE include)
target_link_libraries(geantinoB5 PRIVATE ${Geant4_LIBRARIES})

# Copia a macro de teste para a pasta de build: ./geantinoB5 run_batch_exemplo.mac
configure_file(${PROJECT_SOURCE_DIR}/macros/run_batch_exemplo.mac
               ${PROJECT_BINARY_DIR}/run_batch_exemplo.mac COPYONLY)
